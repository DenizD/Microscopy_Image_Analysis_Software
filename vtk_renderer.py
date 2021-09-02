import vtk

class VTK_Renderer():
    
    # fileName should be a .tif file with (z,y,x) ordering
    def __init__(self, mainWindow, vtkWidget, fileName, spacing=[20,20,20]):
        self.mainWindow = mainWindow
        self.vtkWidget = vtkWidget
        self.fileName = fileName
        self.spacing = spacing

        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()

        imageName = self.fileName.split("/")[-1]
        imageExtension = imageName[-3:]
        imageName = imageName[:-4]

        assert imageExtension == 'tif', 'Image should be a tif file'

        self.reader = vtk.vtkTIFFReader()
        self.reader.SetFileName(self.fileName)
        self.reader.SetDataSpacing(*self.spacing)
        self.reader.SetDataOrigin(0.0, 0.0, 0.0)
        self.reader.SetDataScalarTypeToUnsignedShort()
        self.reader.UpdateWholeExtent()   


    def init_volume_renderer(self):
        self.vtkImageData = self.reader.GetOutput()

        self.colorFunc = vtk.vtkColorTransferFunction()
        self.colorFunc.AddRGBPoint(1, 0.5, 0.5, 0.5)
        self.opacity = vtk.vtkPiecewiseFunction()

        self.volumeProperty = vtk.vtkVolumeProperty()
        self.volumeProperty.SetColor(self.colorFunc)
        self.volumeProperty.SetScalarOpacity(self.opacity)
        self.volumeProperty.SetInterpolationTypeToLinear()
        self.volumeProperty.SetIndependentComponents(2)

        self.volumeMapper = vtk.vtkOpenGLGPUVolumeRayCastMapper()
        self.volumeMapper.SetInputData(self.vtkImageData)
        self.volumeMapper.SetBlendModeToMaximumIntensity()

        self.volume = vtk.vtkVolume()
        self.volume.SetMapper(self.volumeMapper)
        self.volume.SetProperty(self.volumeProperty)

        self.volumeRenderer = vtk.vtkRenderer()
        self.volumeRenderer.AddVolume(self.volume)
        self.volumeRenderer.SetBackground(0,0,0)
        self.volumeRenderer.ResetCamera()

    # callback for changing the color of the volume
    def slider_callback(self, value):
        newValue = value / 5;
        sliderName = self.mainWindow.sender().name
        
        r,g,b = self.volumeProperty.GetRGBTransferFunction().GetColor(0)

        colorFunc = vtk.vtkColorTransferFunction()
        if sliderName == 'red':
            colorFunc.AddRGBPoint(1, 0.5+newValue, g, b)
        elif sliderName == 'green':
            colorFunc.AddRGBPoint(2, r, 0.5+newValue, b)
        elif sliderName == 'blue':
            colorFunc.AddRGBPoint(3, r, g, 0.5+newValue)

        self.volumeProperty.SetColor(colorFunc)
        self.vtkWidget.GetRenderWindow().Render()


    def init_slice_renderer(self):      
        # center of the volume calculation
        self.reader.Update()
        (xMin, xMax, yMin, yMax, zMin, zMax) = self.reader.GetExecutive().GetWholeExtent(self.reader.GetOutputInformation(0))

        (xSpacing, ySpacing, zSpacing) = self.reader.GetOutput().GetSpacing()
        (x0, y0, z0) = self.reader.GetOutput().GetOrigin()
        
        center = [x0 + xSpacing * 0.5 * (xMin + xMax),
                  y0 + ySpacing * 0.5 * (yMin + yMax),
                  z0 + zSpacing * 0.5 * (zMin + zMax)]
        
        # coronal and sagittal view matrices
        coronal = vtk.vtkMatrix4x4()
        coronal.DeepCopy((1, 0, 0, center[0],
                         0, -1, 0, center[1],
                         0, 0,  1, center[2],
                         0, 0,  0, 1))

        sagittal = vtk.vtkMatrix4x4()
        sagittal.DeepCopy((0, 0,-1, center[0],
                           1, 0, 0, center[1],
                           0,-1, 0, center[2],
                           0, 0, 0, 1))

        # slices in the selected orientation (coronal or sagittal)
        self.reslice = vtk.vtkImageReslice()
        self.reslice.SetInputConnection(self.reader.GetOutputPort())
        self.reslice.SetOutputDimensionality(2)
        self.reslice.SetResliceAxes(coronal)
        self.reslice.SetInterpolationModeToLinear()
        
        # grayscale lookup table
        table = vtk.vtkLookupTable()
        table.SetRange(0, 5000) # intensity range
        table.SetValueRange(0.0, 1.0) # from black to white
        table.SetSaturationRange(0.0, 0.0)
        table.SetRampToLinear()
        table.Build()
        
        color = vtk.vtkImageMapToColors()
        color.SetLookupTable(table)
        color.SetInputConnection(self.reslice.GetOutputPort())
        
        actor = vtk.vtkImageActor()
        actor.GetMapper().SetInputConnection(color.GetOutputPort())
        
        self.sliceRenderer = vtk.vtkRenderer()
        self.sliceRenderer.AddActor(actor)
        
        # add callbacks for moving the image slices
        self.actions = {}
        self.actions["Slicing"] = 0

        self.interactorStyle = vtk.vtkInteractorStyleImage()
        self.interactorStyle.AddObserver("MouseMoveEvent", self.__MouseMoveCallback)
        self.interactorStyle.AddObserver("LeftButtonPressEvent", self.__ButtonCallback)
        self.interactorStyle.AddObserver("LeftButtonReleaseEvent", self.__ButtonCallback)
        self.iren.SetInteractorStyle(self.interactorStyle)

      
    def __ButtonCallback(self, obj, event):
        if event == "LeftButtonPressEvent":
            self.actions["Slicing"] = 1
        else:
            self.actions["Slicing"] = 0


    def __MouseMoveCallback(self, obj, event):
        (lastX, lastY) = self.iren.GetLastEventPosition()
        (mouseX, mouseY) = self.iren.GetEventPosition()
        if self.actions["Slicing"] == 1:
            deltaY = mouseY - lastY
            self.reslice.Update()
            sliceSpacing = self.reslice.GetOutput().GetSpacing()[2]
            matrix = self.reslice.GetResliceAxes()
            
            center = matrix.MultiplyPoint((0, 0, sliceSpacing*deltaY, 1))
            matrix.SetElement(0, 3, center[0])
            matrix.SetElement(1, 3, center[1])
            matrix.SetElement(2, 3, center[2])
            self.vtkWidget.GetRenderWindow().Render()
        else:
            self.interactorStyle.OnMouseMove()