cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(SlicerConda)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/DCBIA-OrthoLab/SlicerConda#readme")
set(EXTENSION_CATEGORY "Conda")
set(EXTENSION_CONTRIBUTORS "Leroux Gaelle (University of Michigan) Claret Jeanne (University of Michigan) Allemang David (kitware)")
set(EXTENSION_DESCRIPTION "This extension simplifies conda integration by managing installation path and providing tools for developpers to execute Conda commands.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/DCBIA-OrthoLab/SlicerConda/main/CondaSetUp/Resources/Icons/CondaSetUp.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/DCBIA-OrthoLab/SlicerConda/main/screenshot/Screenshot2.png")
set(EXTENSION_DEPENDS "NA") # Specified as a list or "NA" if no dependencies

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(CondaSetUp)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
