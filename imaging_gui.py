from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QGridLayout, QFileDialog, QComboBox, QFrame
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from custom_ui_components import CustomButton, CustomLineEdit, CustomSlider
from vtk_renderer import VTK_Renderer
from algorithms import registration
import sys

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        
        self.fixedImageFile = None
        self.movingImageFile = None
        self.transformedMovingImageFile = None
        self.fixedImageSpacing = None
        self.movingImageSpacing = None
        self.currentRenderMode = "volume"
        self.vtkWidgets = {}
        self.vtkRenderers = {}

        self.setWindowTitle("Microscopy Image Registration")

        self.frame = QFrame()
        self.layout = QGridLayout()				   
        self.frame.setLayout(self.layout)
        self.setCentralWidget(self.frame)
        											   
        self.atlasSelectionBtn = CustomButton(self, "Select Atlas (Fixed)", onPressed=self.open_file_selection_dialog, args=["./data", ".tif"])
        self.imageSelectionBtn = CustomButton(self, "Select Image (Moving)", onPressed=self.open_file_selection_dialog, args=["./data", ".tif"])

        self.layout.addWidget(self.atlasSelectionBtn, 0, 0)
        self.layout.addWidget(self.imageSelectionBtn, 0, 1)

        self.show()


    def select_transform_callback(self):
        self.transform = self.comboBox.currentText()

    def value_changed(self, value):
        if self.sender() == self.atlasSpacingInput:
            self.fixedImageSpacing = value
        elif self.sender() == self.imageSpacingInput:
            self.movingImageSpacing = value

    def open_file_selection_dialog(self, args):
        defaultDir = args[0]
        fileExtension = args[1]
 
        pressedBtn = self.sender()

        path = QFileDialog.getOpenFileName(self, "Open a file", defaultDir, f"{fileExtension} files (*{fileExtension}*)")

        if path != ("", ""):
            if pressedBtn == self.atlasSelectionBtn.btn:
                self.fixedImageFile = path[0]
                self.fixedImageName = self.fixedImageFile.split("/")[-1]
                self.atlasSelectionBtn.label.setText(self.fixedImageName)
                self.init_vtk_object(imageFile=self.fixedImageFile, imageType="fixed", layoutY=1, layoutX=0, renderMode=self.currentRenderMode)

            elif pressedBtn == self.imageSelectionBtn.btn:
                self.movingImageFile = path[0]
                self.movingImageName = self.movingImageFile.split("/")[-1]
                self.imageSelectionBtn.label.setText(self.movingImageName)
                self.init_vtk_object(imageFile=self.movingImageFile, imageType="moving", layoutY=1, layoutX=1, renderMode=self.currentRenderMode)
            
            self.resize(1440, 800)

        if self.fixedImageFile and self.movingImageFile:
            self.renderModeBtn = CustomButton(self, "Toggle Render Mode", onPressed=self.change_render_mode)
            self.layout.addWidget(self.renderModeBtn, 5, 0)
            self.add_registration_ui()


    def add_registration_ui(self):
        self.layout.addWidget(QLabel("Select Transform"), 6, 0)
        transformList = [
            "Translation", 
            "Rigid", 
            "Similarity", 
            "QuickRigid", 
            "DenseRigid", 
            "BOLDRigid",
            "Affine",
            "AffineFast",
            "BOLDAffine",
            "TRSAA",
            "ElasticSyN",
            "SyN",
            "SyNRA",
            "SyNOnly",
            "SyNabp",
            "SyNBold",
            "SyNBoldAff",
            "SyNAggro",
            "TVMSQ"
        ]
        self.comboBox = QComboBox(self)
        self.comboBox.addItems(transformList)
        self.comboBox.activated.connect(self.select_transform_callback)
        self.transform = self.comboBox.currentText()
        self.layout.addWidget(self.comboBox, 7, 0)

        self.atlasSpacingInput = CustomLineEdit(self, "Fixed Image Spacing (um)", onChanged=self.value_changed)
        self.imageSpacingInput = CustomLineEdit(self, "Moving Image Spacing (um)", onChanged=self.value_changed)
        self.layout.addWidget(self.atlasSpacingInput, 8, 0)
        self.layout.addWidget(self.imageSpacingInput, 9, 0)

        self.runRegistrationBtn = QPushButton("Run Registration")
        self.runRegistrationBtn.clicked.connect(self.run_registration)
        self.layout.addWidget(self.runRegistrationBtn, 9, 1)

    def change_render_mode(self):
        pressedBtn = self.sender()

        if pressedBtn == self.renderModeBtn.btn:
            if self.currentRenderMode == "volume":
                self.currentRenderMode = "slice"
            elif self.currentRenderMode == "slice":
                self.currentRenderMode = "volume"

            self.init_vtk_object(imageFile=self.fixedImageFile, imageType="fixed", layoutY=1, layoutX=0, renderMode=self.currentRenderMode)
            self.init_vtk_object(imageFile=self.movingImageFile, imageType="moving", layoutY=1, layoutX=1, renderMode=self.currentRenderMode)

            if self.transformedMovingImageFile:
                self.init_vtk_object(imageFile=self.transformedMovingImageFile, imageType="transformed", layoutY=1, layoutX=2, renderMode=self.currentRenderMode)

    def init_vtk_object(self, imageFile, imageType, layoutY, layoutX, renderMode):
        vtkWidget = QVTKRenderWindowInteractor(self.frame)
        vtkRenderer = VTK_Renderer(self, vtkWidget, imageFile)
        self.vtkWidgets[imageType] = vtkWidget
        self.vtkRenderers[imageType] = vtkRenderer
        self.add_vtk_object(self.vtkWidgets[imageType], self.vtkRenderers[imageType], layoutY=layoutY, layoutX=layoutX, renderMode=renderMode)

    def add_vtk_object(self, vtkWidget, vtkRenderer, layoutY, layoutX, renderMode):
        if renderMode == "volume":
            vtkRenderer.init_volume_renderer()
            vtkWidget.GetRenderWindow().AddRenderer(vtkRenderer.volumeRenderer)

            self.sliderR = CustomSlider(self, "red", valueChanged=vtkRenderer.slider_callback)
            self.sliderG = CustomSlider(self, "green", valueChanged=vtkRenderer.slider_callback)
            self.sliderB = CustomSlider(self, "blue", valueChanged=vtkRenderer.slider_callback)

            self.layout.addWidget(self.sliderR, layoutY, layoutX)
            self.layout.addWidget(self.sliderG, layoutY+1, layoutX)
            self.layout.addWidget(self.sliderB, layoutY+2, layoutX)

        elif renderMode == "slice":
            vtkRenderer.init_slice_renderer()
            vtkWidget.GetRenderWindow().AddRenderer(vtkRenderer.sliceRenderer)
        
        vtkRenderer.iren.Initialize()
        self.layout.addWidget(vtkWidget, layoutY+3, layoutX)

    def run_registration(self):
        if self.fixedImageFile and self.movingImageFile and self.fixedImageSpacing and self.movingImageSpacing:
            self.transformedMovingImageFile, self.transformedFixedImageFile = registration.run(fixedImageFile = self.fixedImageFile, 
                                    movingImageFile = self.movingImageFile,
                                    fixedImageSpacing = tuple([int(self.fixedImageSpacing)]*3),
                                    movingImageSpacing = tuple([int(self.movingImageSpacing)]*3),
                                    transform = self.transform)

            self.layout.addWidget(QLabel("Transformed Image"), 0, 2)
            self.init_vtk_object(imageFile=self.transformedMovingImageFile, imageType="transformed", layoutY=1, layoutX=2, renderMode=self.currentRenderMode)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())