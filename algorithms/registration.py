import ants
import numpy as np
import tifffile as tif

class Image_Reg:
    
    def __init__(self, fixedImgNd, movingImgNd, fixedImgSpacing, movingImgSpacing, transform):
        self.fixedImgAnts = self.__numpy2ants(fixedImgNd)
        self.movingImgAnts = self.__numpy2ants(movingImgNd)
        self.fixedImgSpacing = fixedImgSpacing
        self.movingImgSpacing = movingImgSpacing
        self.fixedImgAnts.set_spacing(fixedImgSpacing)
        self.movingImgAnts.set_spacing(movingImgSpacing)
        self.transform = transform

    def __numpy2ants(self, imgNd):
        imgNd = imgNd.astype(np.float32)
        imgNd = np.moveaxis(imgNd, [0,1,2], [2,1,0]) # (z,y,x) -> (x,y,z)
        imgAnts = ants.from_numpy(imgNd)

        return imgAnts

    def __ants2numpy(self, imgAnts):
        imgNd = imgAnts.numpy()
        imgNd = np.moveaxis(imgNd, [0,1,2], [2,1,0]) # (x,y,z) -> (z,y,x)
        imgNd = imgNd.astype(np.uint16)

        return imgNd

    def run_registration(self):
        self.reg = ants.registration(fixed=self.fixedImgAnts, moving=self.movingImgAnts, type_of_transform=self.transform)

        self.transformedImgFixedNd = self.__ants2numpy(self.reg["warpedfixout"])
        self.transformedImgMovingNd = self.__ants2numpy(self.reg["warpedmovout"])  

        return self.transformedImgMovingNd, self.transformedImgFixedNd


def run(fixedImageFile, movingImageFile, fixedImageSpacing, movingImageSpacing, transform):
	print(f'Parameters:\n\
            Fixed Image File: {fixedImageFile}\n\
            Moving Image File: {movingImageFile}\n\
            Fixed Image Spacing: {fixedImageSpacing}\n\
            Moving Image Spacing: {movingImageSpacing}\n\
            Transform: {transform}')

	fixedImageNd = tif.imread(fixedImageFile)
	movingImageNd = tif.imread(movingImageFile)

	imageReg = Image_Reg(fixedImageNd, movingImageNd, fixedImageSpacing, movingImageSpacing, transform)
	transformedMovingImgNd, transformedFixedImgNd = imageReg.run_registration()

	transformedMovingImageFile = "transformed_moving_" + transform + ".tif"
	transformedFixedImageFile = "transformed_fixed_" + transform + ".tif"

	tif.imwrite(transformedMovingImageFile, transformedMovingImgNd, photometric='minisblack')
	tif.imwrite(transformedFixedImageFile, transformedFixedImgNd, photometric='minisblack')

	return transformedMovingImageFile, transformedFixedImageFile
