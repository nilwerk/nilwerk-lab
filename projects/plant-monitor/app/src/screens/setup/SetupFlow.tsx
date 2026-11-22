// Device setup flow S10-S16. Requirements: FR-A03, FR-D03, FR-A04, FR-A05, FR-A02, FR-D02, NFR-03 (<= 3 min target, timer shown), NFR-06 (Wi-Fi password only handed to the sensor).
// Talks to the sensor and the cloud only through SetupServices (ProvisioningService, PlantSetupService, PhotoSource): fakes now, real BLE in a later slice (dev build).
// A-023: no hub pairing step (S17 is v1.1).
import React, { useCallback, useEffect, useReducer, useRef, useState } from 'react';
import { ProvisioningError, type DiscoveredDevice, type LinkState, type PlantDetails, type ProvisioningErrorCode, type SetupServices, type WifiNetwork } from '../../provisioning/types';
import { elapsedSeconds, formatClock, initialSetup, setupReducer } from './setupState';
import { ConnectStep, DetailsStep, DoneStep, LinkedStep, LinkErrorStep, LinkingStep, MoveChoiceStep, NameStep, PhotoStep, ReadyStep, WifiStep } from './SetupSteps';

const codeOf = (e: unknown): ProvisioningErrorCode => (e instanceof ProvisioningError ? e.code : 'unknown');

export function SetupFlow({ services, onExit, now = Date.now }: { services: SetupServices; onExit: () => void; now?: () => number }) {
  const { provisioning, plants, photos } = services;
  const [s, dispatch] = useReducer(setupReducer, undefined, () => initialSetup(now()));
  const [, setTick] = useState(0); // re-render once a second so the clock advances
  const alive = useRef(true);
  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);
  useEffect(() => { if (s.step === 'done') return; const id = setInterval(() => setTick((n) => n + 1), 1000); return () => clearInterval(id); }, [s.step, now]);
  const time = formatClock(elapsedSeconds(s, now()));

  const [scanning, setScanning] = useState(false);
  const [scanned, setScanned] = useState(false);
  const [found, setFound] = useState<DiscoveredDevice[]>([]);
  const [readyError, setReadyError] = useState<ProvisioningErrorCode | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [connectError, setConnectError] = useState<ProvisioningErrorCode | null>(null);
  const [networks, setNetworks] = useState<WifiNetwork[]>([]);
  const [loadingNets, setLoadingNets] = useState(false);
  const [link, setLink] = useState<LinkState | null>(null);
  const [photoCancelled, setPhotoCancelled] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState(false);
  /** N2: the sensor already has a plant; the details wait here until the user chooses. Nothing is written before that. */
  const [pendingMove, setPendingMove] = useState<PlantDetails | null>(null);
  /** after a failed save the device is re-read before anything else: 'linked' = the save may have committed (keep only, no move, no retry); 'unknown' = the re-read failed (keep only) */
  const [recheck, setRecheck] = useState<'linked' | 'unknown' | null>(null);

  const cancel = useCallback(() => { provisioning.disconnect().catch(() => undefined); onExit(); }, [provisioning, onExit]);

  const find = async () => {
    setScanning(true); setReadyError(null); setScanned(false);
    try { const r = await provisioning.scan(); if (alive.current) setFound(r); } catch (e) { if (alive.current) { setFound([]); setReadyError(codeOf(e)); } }
    if (alive.current) { setScanning(false); setScanned(true); }
  };
  const connect = async (pop: string) => {
    if (!s.deviceName) return;
    setConnecting(true); setConnectError(null);
    try { await provisioning.connect(s.deviceName, pop); if (alive.current) dispatch({ type: 'connected' }); } catch (e) { if (alive.current) setConnectError(codeOf(e)); }
    if (alive.current) setConnecting(false);
  };
  useEffect(() => {
    if (s.step !== 'wifi') return;
    setLoadingNets(true);
    provisioning.scanWifi().then((n) => alive.current && setNetworks(n), () => alive.current && setNetworks([])).then(() => alive.current && setLoadingNets(false));
  }, [s.step, provisioning]);

  const linking = s.step === 'linking';
  useEffect(() => {
    if (!linking) return;
    setLink(null);
    provisioning.provision({ ssid: s.ssid, passphrase: s.passphrase, name: s.sensorName }, (st) => alive.current && setLink(st)).then(
      (r) => alive.current && dispatch({ type: 'linked', deviceId: r.deviceId }),
      (e) => alive.current && dispatch({ type: 'linkFailed', error: codeOf(e) }),
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps -- run once per entry into 'linking'
  }, [linking]);

  const pick = async (take: boolean) => {
    setPhotoCancelled(false);
    const uri = await (take ? photos.takePhoto() : photos.pickFromLibrary()).catch(() => null);
    if (!alive.current) return;
    if (uri) dispatch({ type: 'photo', uri }); else setPhotoCancelled(true);
  };
  const save = async (d: PlantDetails, moveFromCurrent = false) => {
    if (!s.deviceId) return;
    setSaving(true); setSaveError(false); setRecheck(null);
    try {
      const r = await plants.createPlant(s.deviceId, d, s.photoUri, { moveFromCurrent });
      if (!alive.current) return;
      if (r.status === 'saved') dispatch({ type: 'saved', plantName: d.name, now: now() });
      else setPendingMove(d);   // already linked: ask, do not move
    } catch {
      if (alive.current) {
        // the save may have committed although its answer was lost: re-read the device BEFORE the user can act again (busy until then)
        setSaveError(true);
        let cur: string | null | 'unknown';
        try { cur = await plants.currentPlant(s.deviceId); } catch { cur = 'unknown'; }
        if (alive.current) {
          setPendingMove(null);
          if (cur === 'unknown') setRecheck('unknown');
          else if (cur !== null) setRecheck('linked');   // on a plant now: keep only, never a second plant
        }
      }
    }
    if (alive.current) setSaving(false);
  };

  const restart = () => { provisioning.disconnect().catch(() => undefined); setPendingMove(null); setRecheck(null); setFound([]); setScanned(false); setReadyError(null); setConnectError(null); setPhotoCancelled(false); setSaveError(false); dispatch({ type: 'restart', now: now() }); };

  switch (s.step) {
    case 'ready': return <ReadyStep time={time} scanning={scanning} scanned={scanned} found={found} error={readyError} onFind={find} onPick={(d) => { setConnectError(null); dispatch({ type: 'chooseDevice', deviceName: d.name }); }} onCancel={cancel} />;
    case 'connect': return <ConnectStep time={time} deviceName={s.deviceName ?? ''} busy={connecting} error={connectError} onConnect={connect} onCancel={cancel} />;
    case 'wifi': return <WifiStep key={s.ssid} time={time} networks={networks} loading={loadingNets} initialSsid={s.ssid} onContinue={(ssid, pw) => dispatch({ type: 'wifiChosen', ssid, passphrase: pw })} onCancel={cancel} />;
    case 'name': return <NameStep time={time} onSubmit={(name) => dispatch({ type: 'startLink', sensorName: name })} onCancel={cancel} />;
    case 'linking': return <LinkingStep time={time} wifiJoined={link === 'claiming' || link === 'claimed'} claimed={link === 'claimed'} />;
    case 'linkError': return <LinkErrorStep time={time} code={s.error ?? 'unknown'} ssid={s.ssid} onReenter={() => dispatch({ type: 'reenterWifi' })} onOther={() => dispatch({ type: 'chooseOtherWifi' })} onRetry={() => dispatch({ type: 'retryLink' })} onStartOver={restart} />;
    case 'photo': return <PhotoStep time={time} cancelled={photoCancelled} onTake={() => pick(true)} onPick={() => pick(false)} supported={photos.supported !== false} onSkip={() => dispatch({ type: 'photo', uri: null })} />;
    case 'details':
      if (recheck) return <LinkedStep unknown={recheck === 'unknown'} onLeave={onExit} />;
      if (pendingMove) return <MoveChoiceStep time={time} busy={saving} error={saveError} onKeep={onExit} onMove={() => save(pendingMove, true)} />;
      return <DetailsStep time={time} busy={saving} error={saveError} onSave={(d) => save(d)} onBack={() => dispatch({ type: 'backToPhoto' })} />;
    case 'done': return <DoneStep plantName={s.plantName ?? ''} time={time} onDone={onExit} onAnother={restart} />;
  }
}
