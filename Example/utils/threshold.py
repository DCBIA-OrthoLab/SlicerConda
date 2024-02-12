import sys
import SimpleITK as sitk

def main(input, threshold, output):

    reader = sitk.ImageFileReader()
    reader.SetFileName(input)
    image = reader.Execute()


    if image.GetNumberOfComponentsPerPixel() > 1:
        image = sitk.VectorMagnitude(image)


    thresholdFilter = sitk.BinaryThresholdImageFilter()
    thresholdFilter.SetLowerThreshold(threshold)
    thresholdFilter.SetUpperThreshold(255)
    thresholdFilter.SetOutsideValue(0)
    thresholdFilter.SetInsideValue(255)
    image = thresholdFilter.Execute(image)


    writer = sitk.ImageFileWriter()
    writer.SetFileName(output)
    writer.Execute(image)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: TemplateKey <input> <threshold> <output>")
        sys.exit(1)
    main(sys.argv[1], int(sys.argv[2]), sys.argv[3])
