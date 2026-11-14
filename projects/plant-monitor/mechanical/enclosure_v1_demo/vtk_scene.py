"""Small offscreen VTK renderer (z-buffer, smooth shading) for the v1 demo hero/exploded PNGs. Needs a display: run through xvfb-run."""
import numpy as np
import vtk
from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray


def _actor(mesh, color, translate=(0, 0, 0), opacity=1.0):
    pts = numpy_to_vtk(np.ascontiguousarray(mesh.vertices, dtype=np.float64), deep=True)
    vp = vtk.vtkPoints(); vp.SetData(pts)
    cells = np.hstack([np.full((len(mesh.faces), 1), 3), mesh.faces]).astype(np.int64).ravel()
    ca = vtk.vtkCellArray(); ca.SetCells(len(mesh.faces), numpy_to_vtkIdTypeArray(cells, deep=True))
    pd = vtk.vtkPolyData(); pd.SetPoints(vp); pd.SetPolys(ca)
    nrm = vtk.vtkPolyDataNormals(); nrm.SetInputData(pd); nrm.SetFeatureAngle(35); nrm.SplittingOn(); nrm.Update()
    mp = vtk.vtkPolyDataMapper(); mp.SetInputConnection(nrm.GetOutputPort())
    a = vtk.vtkActor(); a.SetMapper(mp)
    p = a.GetProperty(); p.SetColor(*color); p.SetOpacity(opacity); p.SetAmbient(0.25); p.SetDiffuse(0.75); p.SetSpecular(0.15); p.SetSpecularPower(20)
    a.SetPosition(*translate)
    return a


def render(items, path, size=(1500, 1000), azimuth=-62, elevation=34, bg=(1, 1, 1), zoom=1.0):
    """items: list of (trimesh, rgb 0..1, (dx,dy,dz), opacity)."""
    ren = vtk.vtkRenderer(); ren.SetBackground(*bg)
    for m, c, t, o in items:
        ren.AddActor(_actor(m, c, t, o))
    ren.UseFXAAOn()
    win = vtk.vtkRenderWindow(); win.AddRenderer(ren); win.SetSize(*size); win.SetMultiSamples(0)
    cam = ren.GetActiveCamera()
    ren.ResetCamera()
    b = ren.ComputeVisiblePropBounds(); ctr = [(b[0] + b[1]) / 2, (b[2] + b[3]) / 2, (b[4] + b[5]) / 2]
    cam.SetFocalPoint(*ctr); cam.SetPosition(ctr[0], ctr[1] - 1, ctr[2]); cam.SetViewUp(0, 0, 1)
    cam.Azimuth(azimuth + 90); cam.Elevation(elevation)
    ren.ResetCamera(); cam.Zoom(zoom)
    ren.RemoveAllLights(); ren.AutomaticLightCreationOff()
    for pos, inten in (((-1, -1.5, 2.5), 0.9), ((1.5, 0.5, 1.2), 0.45), ((0, 2, 0.5), 0.25)):
        l = vtk.vtkLight(); l.SetLightTypeToSceneLight(); l.SetPosition(*[ctr[i] + 200 * pos[i] for i in range(3)]); l.SetFocalPoint(*ctr); l.SetIntensity(inten); ren.AddLight(l)
    win.Render()
    w2i = vtk.vtkWindowToImageFilter(); w2i.SetInput(win); w2i.ReadFrontBufferOn(); w2i.ShouldRerenderOff(); w2i.Update()
    wr = vtk.vtkPNGWriter(); wr.SetFileName(str(path)); wr.SetInputConnection(w2i.GetOutputPort()); wr.Write()
