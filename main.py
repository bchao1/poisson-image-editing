import cv2
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import scipy.sparse

import utils

class PoissonImageBlender:
    def __init__(self, dataset_root):
        self.mask = utils.read_image(f"{dataset_root}", "mask", scale=1, gray=True)
        self.src_rgb = utils.read_image(f"{dataset_root}", "source", scale=1, gray=False)
        self.target_rgb = utils.read_image(f"{dataset_root}", "target", scale=1,  gray=False)
        

        self.img_h, self.img_w = self.mask.shape

        self.mask = np.where(self.mask > 0, 1, 0) # binary 0, 1 mask
        self.inner_mask, self.boundary_mask, self.outer_mask = utils.process_mask(self.mask)
        
        self.pixel_ids = utils.get_pixel_ids(self.mask) 
        self.inner_ids = utils.get_masked_values(self.pixel_ids, self.inner_mask).flatten()
        self.outer_ids = utils.get_masked_values(self.pixel_ids, self.outer_mask).flatten()
        self.boundary_ids = utils.get_masked_values(self.pixel_ids, self.boundary_mask).flatten()
        self.mask_ids = utils.get_masked_values(self.pixel_ids, self.mask).flatten() # boundary + inner
        
        self.inner_pos = np.searchsorted(self.mask_ids, self.inner_ids) 
        self.boundary_pos = np.searchsorted(self.mask_ids, self.boundary_ids)
        self.mask_pos = np.searchsorted(self.pixel_ids.flatten(), self.mask_ids)

        self.A = self.construct_A_matrix()

    def construct_A_matrix(self):
        A = scipy.sparse.lil_matrix((len(self.mask_ids), len(self.mask_ids)))

        n1 = self.inner_ids - 1
        n2 = self.inner_ids + 1
        n3 = self.inner_ids - self.img_w 
        n4 = self.inner_ids + self.img_w

        n1_pos = np.searchsorted(self.mask_ids, n1)
        n2_pos = np.searchsorted(self.mask_ids, n2)
        n3_pos = np.searchsorted(self.mask_ids, n3)
        n4_pos = np.searchsorted(self.mask_ids, n4)

        A[self.inner_pos, n1_pos] = 1
        A[self.inner_pos, n2_pos] = 1
        A[self.inner_pos, n3_pos] = 1
        A[self.inner_pos, n4_pos] = 1
        A[self.inner_pos, self.inner_pos] = -4 

        A[self.boundary_pos, self.boundary_pos] = 1
        return A
    
    def construct_b(self, inner_gradient_values, boundary_pixel_values):
        b = np.zeros(len(self.mask_ids))
        b[self.inner_pos] = inner_gradient_values
        b[self.boundary_pos] = boundary_pixel_values
        return b

    def compute_mixed_gradients(self, src, target, mode="max", alpha=1.0):
        if mode == "max":
            Ix_src, Iy_src = utils.compute_gradient(src)
            Ix_target, Iy_target = utils.compute_gradient(target)
            I_src_amp = np.sqrt(Ix_src**2 + Iy_src**2)
            I_target_amp = np.sqrt(Ix_target**2 + Iy_target**2)
            Ix = np.where(I_src_amp > I_target_amp, Ix_src, Ix_target)
            Iy = np.where(I_src_amp > I_target_amp, Iy_src, Iy_target)
            Ixx, _ = utils.compute_gradient(Ix, forward=False)
            _, Iyy = utils.compute_gradient(Iy, forward=False)
            return Ixx + Iyy
        elif mode == "alpha":
            src_laplacian = utils.compute_laplacian(src)
            arget_laplacian = utils.compute_laplacian(target)
            return alpha * src_laplacian + (1 - alpha) * target_laplacian
        else:
            raise ValueError(f"Gradient mixing mode '{mode}' not supported!")

    def poisson_blend_channel(self, src, target):
        mixed_gradients = self.compute_mixed_gradients(src, target, mode="max")

        boundary_pixel_values = utils.get_masked_values(target, self.boundary_mask).flatten()
        inner_gradient_values = utils.get_masked_values(mixed_gradients, self.inner_mask).flatten()

        # Construct b
        b = self.construct_b(inner_gradient_values, boundary_pixel_values)

        # Solve Ax = b
        x = scipy.sparse.linalg.lsmr(self.A, b)[0]
        new_src = np.zeros_like(src).flatten()
        new_src[self.mask_pos] = x
        new_src = new_src.reshape(src.shape)
        poisson_blended_img = utils.get_alpha_blended_img(new_src, target, self.mask)

        poisson_blended_img = np.clip(poisson_blended_img, 0, 1)
        
        return poisson_blended_img
    
    def poisson_blend_rgb(self):
        poisson_blended_img_rgb = []
        for i in range(self.src_rgb.shape[-1]):
            print(f"Blending channel {i} ...")
            poisson_blended_img_rgb.append(self.poisson_blend_channel(self.src_rgb[..., i], self.target_rgb[..., i]))
        return np.dstack(poisson_blended_img_rgb)
    
    def poisson_blend_gray(self):
        src_gray = utils.rgb2gray(self.src_rgb)
        target_gray = utils.rgb2gray(self.target_rgb)
        return self.poisson_blend_channel(src_gray, target_gray)

if __name__ == "__main__":
    blender = PoissonImageBlender("data/test4/")
    img = blender.poisson_blend_rgb()
    print(img.shape)
    plt.imshow(img)
    plt.show()

