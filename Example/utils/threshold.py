import sys
import SimpleITK as sitk

def main(input, threshold, output):
    # Lecture de l'image
    reader = sitk.ImageFileReader()
    reader.SetFileName(input)
    image = reader.Execute()

    # Vérifie si l'image est en couleur (vecteur) et la convertit en niveaux de gris si nécessaire
    if image.GetNumberOfComponentsPerPixel() > 1:
        image = sitk.VectorMagnitude(image)

    # Application du seuillage
    thresholdFilter = sitk.BinaryThresholdImageFilter()
    thresholdFilter.SetLowerThreshold(threshold)
    thresholdFilter.SetUpperThreshold(255)  # Vous pouvez ajuster cela si nécessaire
    thresholdFilter.SetOutsideValue(0)  # Valeur pour les pixels en dehors du seuil
    thresholdFilter.SetInsideValue(255)  # Valeur pour les pixels à l'intérieur du seuil
    image = thresholdFilter.Execute(image)

    # Sauvegarde de l'image
    writer = sitk.ImageFileWriter()
    writer.SetFileName(output)
    writer.Execute(image)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: TemplateKey <input> <threshold> <output>")
        sys.exit(1)
    main(sys.argv[1], int(sys.argv[2]), sys.argv[3])
