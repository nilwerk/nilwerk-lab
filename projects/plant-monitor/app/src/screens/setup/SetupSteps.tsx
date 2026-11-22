// S10-S16 device setup steps. Requirements: FR-A03 (find sensor, Wi-Fi, name, photo, plant details), FR-D03 (BLE setup, claim), FR-D02 (first report within the hour),
// FR-D07 (reset hint), FR-A04 (6 plant fields), FR-A05 (setup photo), FR-A02 (add another, no cap), NFR-03 (3-minute target), NFR-06 (Wi-Fi password only to the sensor).
// A-023: no hub pairing step (S17 is v1.1). Presentational only: all Bluetooth and cloud work happens in SetupFlow through the service interfaces.
import React, { useState } from 'react';
import { ActivityIndicator, Text, View } from 'react-native';
import { Body, Button, Choice, Field, Notice, Screen } from '../../ui/primitives';
import { useTheme } from '../../ui/useTheme';
import { t } from '../../i18n';
import { parseLabel, advertisedName } from '../../provisioning/label';
import { LOCATION_TYPES, SOIL_TYPES, type DiscoveredDevice, type LocationType, type PlantDetails, type ProvisioningErrorCode, type SoilType, type WifiNetwork } from '../../provisioning/types';
import { validateArea, validateCity, validateDeviceName, validatePlantName, validateSpecies, validateSsid, validateWifiPassword, type FieldResult } from '../../validation';
import { STEP_COUNT } from './setupState';

const msg = (e: FieldResult) => (e ? t(e.key, e.params) : null);
const errorText = (code: ProvisioningErrorCode) => t(`setup.error.${code}`) === `setup.error.${code}` ? t('setup.error.unknown') : t(`setup.error.${code}`);

export function Progress({ n, time }: { n: number; time: string }) {
  const th = useTheme();
  return (
    <View accessibilityLabel={t('a11y.setupProgress', { n, total: STEP_COUNT, time })} style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
      <Text style={{ color: th.color.muted, ...th.type.caption }}>{t('setup.step', { n, total: STEP_COUNT })}</Text>
      <Text style={{ color: th.color.muted, ...th.type.label }}>{time}</Text>
    </View>
  );
}

export function ReadyStep({ time, scanning, found, error, scanned, onFind, onPick, onCancel }: {
  time: string; scanning: boolean; found: DiscoveredDevice[]; error: ProvisioningErrorCode | null; scanned: boolean; onFind: () => void; onPick: (d: DiscoveredDevice) => void; onCancel: () => void;
}) {
  return (
    <Screen title={t('setup.ready.title')} onBack={onCancel}>
      <Progress n={1} time={time} />
      <Body>{t('setup.ready.putInSoil')}</Body>
      <Body>{t('setup.ready.pressButton')}</Body>
      <Body>{t('setup.ready.phoneClose')}</Body>
      <Body muted>{t('setup.ready.permissionNote')}</Body>
      {error ? <Notice kind="error" text={errorText(error)} /> : null}
      <Button label={t('setup.findSensor')} onPress={onFind} busy={scanning} />
      {scanning ? <Body muted>{t('setup.ready.scanning')}</Body> : null}
      {found.length > 0 ? <Body>{t('setup.ready.found')}</Body> : null}
      {found.map((d) => <Button key={d.name} label={d.name} a11yLabel={t('setup.ready.device', { name: d.name, bars: d.bars })} variant="secondary" onPress={() => onPick(d)} />)}
      {scanned && !scanning && !error && found.length === 0 ? <Notice kind="error" text={t('setup.ready.none')} /> : null}
      <Body muted>{t('setup.ready.help')}</Body>
    </Screen>
  );
}

export function ConnectStep({ time, deviceName, busy, error, onConnect, onCancel }: {
  time: string; deviceName: string; busy: boolean; error: ProvisioningErrorCode | null; onConnect: (pop: string) => void; onCancel: () => void;
}) {
  const [code, setCode] = useState('');
  const [local, setLocal] = useState<string | null>(null);
  const submit = () => {
    const p = parseLabel(code);
    if (!p) return setLocal(t('setup.connect.invalid'));
    if (advertisedName(p.hwId) !== deviceName) return setLocal(t('setup.connect.mismatch', { name: deviceName }));
    setLocal(null);
    onConnect(p.pop);
  };
  return (
    <Screen title={t('setup.connect.title')} onBack={onCancel}>
      <Progress n={1} time={time} />
      <Body>{deviceName}</Body>
      <Body>{t('setup.connect.body')}</Body>
      <Field label={t('setup.connect.codeLabel')} value={code} onChangeText={(v) => { setCode(v); setLocal(null); }} autoCapitalize="characters" autoCorrect={false} error={local} />
      <Body muted>{t('setup.connect.scanQr')}</Body>
      {error ? <Notice kind="error" text={errorText(error)} /> : null}
      <Button label={t('setup.connect.submit')} onPress={submit} busy={busy} />
    </Screen>
  );
}

export function WifiStep({ time, networks, loading, initialSsid, onContinue, onCancel }: {
  time: string; networks: WifiNetwork[]; loading: boolean; initialSsid: string; onContinue: (ssid: string, passphrase: string) => void; onCancel: () => void;
}) {
  const [ssid, setSsid] = useState(initialSsid);
  const [other, setOther] = useState(false);
  const [pw, setPw] = useState('');
  const [shown, setShown] = useState(false);
  const net = networks.find((n) => n.ssid === ssid);
  const secure = other ? true : net ? net.secure : true;
  const ssidErr = shown ? msg(validateSsid(ssid)) : null;
  const pwErr = shown && secure ? msg(validateWifiPassword(pw)) : null;
  const go = () => {
    setShown(true);
    if (validateSsid(ssid) || (secure && validateWifiPassword(pw))) return;
    onContinue(ssid, secure ? pw : '');
  };
  return (
    <Screen title={t('setup.wifi.title')} onBack={onCancel}>
      <Progress n={2} time={time} />
      {loading ? <Body muted>{t('setup.wifi.scanning')}</Body> : null}
      {!loading && networks.length === 0 ? <Body muted>{t('setup.wifi.none')}</Body> : null}
      {networks.map((n) => <Choice key={n.ssid} label={n.ssid} a11yLabel={t('setup.wifi.network', { ssid: n.ssid, bars: n.bars, lock: n.secure ? t('setup.wifi.locked') : '' })} selected={!other && ssid === n.ssid} onPress={() => { setOther(false); setSsid(n.ssid); }} />)}
      <Choice label={t('setup.wifi.other')} selected={other} onPress={() => { setOther(true); setSsid(''); }} />
      {other ? <Field label={t('setup.wifi.ssidLabel')} value={ssid} onChangeText={setSsid} autoCapitalize="none" autoCorrect={false} error={ssidErr} /> : shown && !ssid ? <Notice kind="error" text={t('validation.ssid.required')} /> : null}
      {secure ? <Field label={t('setup.wifi.passwordLabel')} value={pw} onChangeText={setPw} secureTextEntry autoCapitalize="none" autoCorrect={false} error={pwErr} /> : null}
      <Body muted>{t('setup.wifi.note')}</Body>
      <Button label={t('setup.wifi.continue')} onPress={go} />
    </Screen>
  );
}

export function NameStep({ time, onSubmit, onCancel }: { time: string; onSubmit: (name: string) => void; onCancel: () => void }) {
  const [name, setName] = useState('');
  const [shown, setShown] = useState(false);
  const err = shown ? msg(validateDeviceName(name)) : null;
  return (
    <Screen title={t('setup.name.title')} onBack={onCancel}>
      <Progress n={3} time={time} />
      <Field label={t('setup.name.label')} placeholder={t('setup.name.hint')} value={name} onChangeText={setName} error={err} />
      <Button label={t('setup.name.submit')} onPress={() => { setShown(true); if (!validateDeviceName(name)) onSubmit(name.trim()); }} /* same trimmed string that is validated */ />
    </Screen>
  );
}

export function LinkingStep({ time, wifiJoined, claimed }: { time: string; wifiJoined: boolean; claimed: boolean }) {
  const th = useTheme();
  return (
    <Screen title={t('setup.link.title')}>
      <Progress n={3} time={time} />
      <ActivityIndicator accessibilityLabel={t('common.loading')} color={th.color.accent} />
      <Body>{wifiJoined ? `✓ ${t('setup.link.wifiOk')}` : t('setup.link.joining')}</Body>
      {wifiJoined ? <Body>{claimed ? `✓ ${t('setup.link.claimed')}` : t('setup.link.claiming')}</Body> : null}
    </Screen>
  );
}

export function LinkErrorStep({ time, code, ssid, onReenter, onOther, onRetry, onStartOver }: {
  time: string; code: ProvisioningErrorCode; ssid: string; onReenter: () => void; onOther: () => void; onRetry: () => void; onStartOver: () => void;
}) {
  const [reset, setReset] = useState(false);
  const wifi = code === 'wifi_auth' || code === 'wifi_no_ap' || code === 'wifi_timeout';
  const owned = code === 'device_owned';
  const retryable = code === 'claim_network' || code === 'claim_server';
  const title = wifi ? t('setup.linkError.wifi.title') : owned ? t('setup.linkError.owned.title') : t('setup.linkError.claim.title');
  const key = `setup.linkError.${code}`;
  return (
    <Screen title={title}>
      <Progress n={3} time={time} />
      <Notice kind="error" text={t(key, { ssid })} />
      {wifi ? <><Button label={t('setup.linkError.reenter')} onPress={onReenter} /><Button label={t('setup.linkError.otherNetwork')} variant="secondary" onPress={onOther} /></> : null}
      {owned ? <><Button label={t('setup.linkError.howToReset')} variant="secondary" onPress={() => setReset(true)} />{reset ? <Body>{t('setup.linkError.resetHint')}</Body> : null}</> : null}
      {retryable ? <Button label={t('setup.linkError.retry')} onPress={onRetry} /> : null}
      {!wifi ? <Button label={t('setup.linkError.startOver')} variant={retryable ? 'ghost' : 'primary'} onPress={onStartOver} /> : null}
    </Screen>
  );
}

export function PhotoStep({ time, cancelled, supported = true, onTake, onPick, onSkip }: { time: string; cancelled: boolean; supported?: boolean; onTake: () => void; onPick: () => void; onSkip: () => void }) {
  return (
    <Screen title={t('setup.photo.title')}>
      <Progress n={4} time={time} />
      <Body>{t('setup.photo.body')}</Body>
      {!supported ? <Body muted>{t('setup.photo.unsupported')}</Body> : null}
      {supported && cancelled ? <Body muted>{t('setup.photo.cancelled')}</Body> : null}
      {supported ? <Button label={t('setup.photo.take')} onPress={onTake} /> : null}
      {supported ? <Button label={t('setup.photo.pick')} variant="secondary" onPress={onPick} /> : null}
      <Button label={t('setup.photo.skip')} variant="ghost" onPress={onSkip} />
    </Screen>
  );
}

export function DetailsStep({ time, busy, error, onSave, onBack }: { time: string; busy: boolean; error: boolean; onSave: (d: PlantDetails) => void; onBack: () => void }) {
  const [d, setD] = useState<PlantDetails>({ name: '', location: 'house', area: '', soil: 'potting', species: '', city: '' });
  const [shown, setShown] = useState(false);
  const set = <K extends keyof PlantDetails>(k: K, v: PlantDetails[K]) => setD((p) => ({ ...p, [k]: v }));
  const errs = { name: validatePlantName(d.name), area: validateArea(d.area), city: validateCity(d.city), species: validateSpecies(d.species) };
  const invalid = Object.values(errs).some(Boolean);
  const e = (k: keyof typeof errs) => (shown ? msg(errs[k]) : null);
  return (
    <Screen title={t('setup.details.title')} onBack={onBack}>
      <Progress n={5} time={time} />
      <Field label={t('setup.details.name')} value={d.name} onChangeText={(v) => set('name', v)} error={e('name')} />
      <View accessibilityRole="radiogroup" accessibilityLabel={t('setup.details.location')} style={{ gap: 8 }}>
        <Body muted>{t('setup.details.location')}</Body>
        {LOCATION_TYPES.map((l: LocationType) => <Choice key={l} label={t(`setup.location.${l}`)} selected={d.location === l} onPress={() => set('location', l)} />)}
      </View>
      <Field label={t('setup.details.area')} value={d.area} onChangeText={(v) => set('area', v)} error={e('area')} />
      <View accessibilityRole="radiogroup" accessibilityLabel={t('setup.details.soil')} style={{ gap: 8 }}>
        <Body muted>{t('setup.details.soil')}</Body>
        {SOIL_TYPES.map((s: SoilType) => <Choice key={s} label={t(`setup.soil.${s}`)} selected={d.soil === s} onPress={() => set('soil', s)} />)}
      </View>
      <Field label={t('setup.details.species')} value={d.species} onChangeText={(v) => set('species', v)} error={e('species')} />
      <Field label={t('setup.details.city')} value={d.city} onChangeText={(v) => set('city', v)} error={e('city')} />
      {error ? <Notice kind="error" text={t('setup.details.saveError')} /> : null}
      <Button label={t('setup.details.save')} busy={busy} onPress={() => { setShown(true); if (!invalid) onSave({ ...d, name: d.name.trim(), area: d.area.trim(), species: d.species.trim(), city: d.city.trim() }); }} />
    </Screen>
  );
}

export function DoneStep({ plantName, time, onDone, onAnother }: { plantName: string; time: string; onDone: () => void; onAnother: () => void }) {
  return (
    <Screen title={t('setup.done.title')}>
      <Body>{t('setup.done.body', { plantName })}</Body>
      <Body>{t('setup.done.time', { time })}</Body>
      <Button label={t('setup.done.seePlant')} onPress={onDone} />
      <Button label={t('setup.done.another')} variant="secondary" onPress={onAnother} />
    </Screen>
  );
}
