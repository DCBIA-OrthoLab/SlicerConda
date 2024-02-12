import logging
import os
from typing import Annotated, Optional

import vtk

import slicer
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange,
)

from slicer import vtkMRMLScalarVolumeNode
from qt import QFileDialog,QMessageBox
import time
from CondaSetUp import  CondaSetUpCall # Calling CondaSetUpCall
import threading

from functools import partial
#
# Example
#


class Example(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("Example")  # TODO: make this more human readable by adding spaces
        # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.categories = ["Slicer Conda"]
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["John Doe (AnyWare Corp.)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        # _() function marks text as translatable to other languages
        self.parent.helpText = _("""
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#Example">module documentation</a>.
""")
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = _("""
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""")

        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", registerSampleData)


#
# Register sample data sets in Sample Data module
#


def registerSampleData():
    """Add data sets to Sample Data module."""
    # It is always recommended to provide sample data for users to make it easy to try the module,
    # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

    import SampleData

    iconsPath = os.path.join(os.path.dirname(__file__), "Resources/Icons")

    # To ensure that the source code repository remains small (can be downloaded and installed quickly)
    # it is recommended to store data sets that are larger than a few MB in a Github release.

    # Example1
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="Example",
        sampleName="Example1",
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, "Example1.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        fileNames="Example1.nrrd",
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums="SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        # This node name will be used when the data set is loaded
        nodeNames="Example1",
    )

    # Example2
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="Example",
        sampleName="Example2",
        thumbnailFileName=os.path.join(iconsPath, "Example2.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        fileNames="Example2.nrrd",
        checksums="SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        # This node name will be used when the data set is loaded
        nodeNames="Example2",
    )


#
# ExampleParameterNode
#


@parameterNodeWrapper
class ExampleParameterNode:
    """
    The parameters needed by module.

    inputVolume - The volume to threshold.
    imageThreshold - The value at which to threshold the input volume.
    invertThreshold - If true, will invert the threshold.
    thresholdedVolume - The output volume that will contain the thresholded volume.
    invertedVolume - The output volume that will contain the inverted thresholded volume.
    """

    inputVolume: vtkMRMLScalarVolumeNode
    imageThreshold: Annotated[float, WithinRange(-100, 500)] = 100
    invertThreshold: bool = False
    thresholdedVolume: vtkMRMLScalarVolumeNode
    invertedVolume: vtkMRMLScalarVolumeNode


#
# ExampleWidget
#


class ExampleWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._parameterNodeGuiTag = None

    def setup(self) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/Example.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = ExampleLogic()

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # Buttons
        self.ui.applyButton.connect("clicked(bool)", self.onApplyButton)
        self.ui.horizontalSlider.valueChanged.connect(self.ui.spinBox.setValue)
        self.ui.spinBox.valueChanged.connect(self.ui.horizontalSlider.setValue)

        self.ui.pushButtonOutput.connect("clicked(bool)",partial(self.openFinder,"folder"))
        self.ui.pushButtonInput.connect("clicked(bool)",partial(self.openFinder,"file"))


        self.ui.labelInformation.setHidden(True)


        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

    def openFinder(self,type:str,_):
        if type == "folder":
            surface_folder = QFileDialog.getExistingDirectory(self.parent, "Select a scan folder")
            self.ui.lineEditOutput.setText(surface_folder)
        else :
            surface_folder = QFileDialog.getOpenFileName(self.parent, 'Open a file', '', 'Image files (*.png *.jpeg *.jpg)')
            self.ui.lineEditInput.setText(surface_folder)



    def cleanup(self) -> None:
        """Called when the application closes and the module widget is destroyed."""
        self.removeObservers()

    def enter(self) -> None:
        """Called each time the user opens this module."""
        # Make sure parameter node exists and observed
        self.initializeParameterNode()

    def exit(self) -> None:
        """Called each time the user opens a different module."""
        # Do not react to parameter node changes (GUI will be updated when the user enters into the module)
        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self._parameterNodeGuiTag = None
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)

    def onSceneStartClose(self, caller, event) -> None:
        """Called just before the scene is closed."""
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event) -> None:
        """Called just after the scene is closed."""
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self) -> None:
        """Ensure parameter node exists and observed."""
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())

        # Select default input nodes if nothing is selected yet to save a few clicks for the user
        if not self._parameterNode.inputVolume:
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
            if firstVolumeNode:
                self._parameterNode.inputVolume = firstVolumeNode

    def setParameterNode(self, inputParameterNode: Optional[ExampleParameterNode]) -> None:
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
        self._parameterNode = inputParameterNode
        if self._parameterNode:
            # Note: in the .ui file, a Qt dynamic property called "SlicerParameterName" is set on each
            # ui element that needs connection.
            self._parameterNodeGuiTag = self._parameterNode.connectGui(self.ui)
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
            self._checkCanApply()

    def _checkCanApply(self, caller=None, event=None) -> None:
        if self.ui.lineEditInput!="" and self.ui.lineEditOutput!="" :
            self.ui.applyButton.toolTip = _("Apply threshold")
            self.ui.applyButton.enabled = True
        else:
            self.ui.applyButton.toolTip = _("Select input file and output folder")
            self.ui.applyButton.enabled = False

    def onApplyButton(self) -> None:
        """Run processing when user clicks "Apply" button."""
        conda = CondaSetUpCall() # Creation of the object
        path_conda = conda.getCondaPath() # Get the conda path to find out if the user has entered it
        print("path_conda : ",path_conda)
        if path_conda == "None":
          slicer.util.infoDisplay("Path to conda is no set up. Open the module SlicerConda to do it",windowTitle="Can't found conda path")
        else :
          self.ui.labelInformation.setHidden(False)
          self.ui.labelInformation.setText("Image in process \ntime : 0s")
          start_time = time.time()
          previous_time = start_time
          current_time = time.time()
          elapsed_time = current_time - start_time
          name_env = "example"
          flag = True
          libs = ["SimpleITK"]
          print(conda.condaRunCommand(["conda info --envs"])) # Example of a conda commande to print all the existing environnement
          if not conda.condaTestEnv(name_env): # Example of a conda command to test the existence of a specific environment

            userResponse = slicer.util.confirmYesNoDisplay(f"The environnement {name_env} doesn't exist, do you want to create it ? \nThe libraries {' '.join(lib for lib in libs)} will be installed. ", windowTitle="Env doesn't exist")
            if userResponse :
              process = threading.Thread(target=conda.condaCreateEnv, args=(name_env,"3.9",libs,)) # Example of the creation of a new environment with the installation of a library
              process.start()

              while process.is_alive():
                  slicer.app.processEvents()
                  current_time = time.time()
                  gap=current_time-previous_time
                  if gap>0.3:
                      previous_time = current_time
                      elapsed_time = current_time - start_time
                      self.ui.labelInformation.setText(f"Creation of the new environment. \nThis task may take a few minutes. The libraries {' '.join(lib for lib in libs)} will be installed.\ntime: {elapsed_time:.1f}s")

            else :
                flag = False
                self.ui.labelInformation.setText(f"The process is finished\ntime: {elapsed_time:.1f}s")

          if flag :
            lis_lib_install = conda.condaRunCommand(['conda','list'],name_env) # Example of a command running in a specific environment (here, return the list of libraries installed in the 'example' environment)
            print(f"The list of librairies in {name_env} is : {lis_lib_install}")
            missing_lib = []
            for lib in libs:
                if lib.lower() not in lis_lib_install:
                    missing_lib.append(lib)

            if len(missing_lib) != 0:
                userResponse = slicer.util.confirmYesNoDisplay(f"The environnement {name_env} exist but the libraries : {' '.join(lib for lib in missing_lib)} are missing, do you want to install them ? ", windowTitle="Env doesn't exist")
                if userResponse :
                    process = threading.Thread(target=conda.condaInstallLibEnv, args=(name_env,missing_lib)) # Example of installing certain libraries in a specific environment
                    process.start()

                    while process.is_alive():
                        slicer.app.processEvents()
                        current_time = time.time()
                        gap=current_time-previous_time
                        if gap>0.3:
                            previous_time = current_time
                            elapsed_time = current_time - start_time
                            self.ui.labelInformation.setText(f"The libraries {' '.join(lib for lib in missing_lib)} is being installed in the environment {name_env}. \nThis task may take few minutes\ntime: {elapsed_time:.1f}s")

                else :
                    flag = False
          if flag :
            file_path = os.path.dirname(os.path.abspath(__file__))
            file_to_run = os.path.join(file_path,"utils","threshold.py")
            _, file_extension = os.path.splitext(self.ui.lineEditInput.text)
            arguments = [self.ui.lineEditInput.text,str(self.ui.horizontalSlider.value),os.path.join(self.ui.lineEditOutput.text,(self.ui.lineEditSuffix.text+file_extension))]
            print("args : ",arguments)

            process = threading.Thread(target=conda.condaRunFilePython, args=(file_to_run,arguments,name_env)) # Example of running a python file with input arguments in a specific environment
            process.start()
            while process.is_alive():
                slicer.app.processEvents()
                current_time = time.time()
                gap=current_time-previous_time
                if gap>0.3:
                    previous_time = current_time
                    elapsed_time = current_time - start_time
                    self.ui.labelInformation.setText(f"File in process\ntime: {elapsed_time:.1f}s")


        self.ui.labelInformation.setText(f"The process is finished\ntime: {elapsed_time:.1f}s")
        print(f"The process is finished\ntime: {elapsed_time:.1f}s")








#
# ExampleLogic
#


class ExampleLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self) -> None:
        """Called when the logic class is instantiated. Can be used for initializing member variables."""
        ScriptedLoadableModuleLogic.__init__(self)

    def getParameterNode(self):
        return ExampleParameterNode(super().getParameterNode())

    def process(self,
                inputVolume: vtkMRMLScalarVolumeNode,
                outputVolume: vtkMRMLScalarVolumeNode,
                imageThreshold: float,
                invert: bool = False,
                showResult: bool = True) -> None:
        """
        # Run the processing algorithm.
        # Can be used without GUI widget.
        # :param inputVolume: volume to be thresholded
        # :param outputVolume: thresholding result
        # :param imageThreshold: values above/below this threshold will be set to 0
        # :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
        # :param showResult: show output volume in slice viewers
        # """

        # if not inputVolume or not outputVolume:
        #     raise ValueError("Input or output volume is invalid")

        # import time

        # startTime = time.time()
        # logging.info("Processing started")

        # # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
        # cliParams = {
        #     "InputVolume": inputVolume.GetID(),
        #     "OutputVolume": outputVolume.GetID(),
        #     "ThresholdValue": imageThreshold,
        #     "ThresholdType": "Above" if invert else "Below",
        # }
        # cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True, update_display=showResult)
        # # We don't need the CLI module node anymore, remove it to not clutter the scene with it
        # slicer.mrmlScene.RemoveNode(cliNode)

        # stopTime = time.time()
        # logging.info(f"Processing completed in {stopTime-startTime:.2f} seconds")
        print("There is no pocess here in this module")


#
# ExampleTest
#


class ExampleTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """Do whatever is needed to reset the state - typically a scene clear will be enough."""
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here."""
        self.setUp()
        self.test_Example1()

    def test_Example1(self):
        """Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")

        # Get/create input data

        # import SampleData

        # registerSampleData()
        # inputVolume = SampleData.downloadSample("Example1")
        # self.delayDisplay("Loaded test data set")

        # inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        # self.assertEqual(inputScalarRange[0], 0)
        # self.assertEqual(inputScalarRange[1], 695)

        # outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        # threshold = 100

        # # Test the module logic

        # logic = ExampleLogic()

        # # Test algorithm with non-inverted threshold
        # logic.process(inputVolume, outputVolume, threshold, True)
        # outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        # self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        # self.assertEqual(outputScalarRange[1], threshold)

        # # Test algorithm with inverted threshold
        # logic.process(inputVolume, outputVolume, threshold, False)
        # outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        # self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        # self.assertEqual(outputScalarRange[1], inputScalarRange[1])

        self.delayDisplay("Test passed")
