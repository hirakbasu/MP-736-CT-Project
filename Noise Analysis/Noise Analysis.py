import matplotlib.pyplot as plt
import numpy as np
import tifffile
from scipy import ndimage
import os
import time

# load images (noiseless recon, 0 TCM, 0.5 TCM, 1.0 TCM)
# define phantom
phantom_name = 'F41BMI'
subject_path = f'D:/CT TCM/{phantom_name}/'

noiseless = tifffile.imread(subject_path + f'{phantom_name}_Noiseless.tif')
noise00 = tifffile.imread(subject_path + '00 Noise.tif')
noise05 = tifffile.imread(subject_path + '05 Noise.tif')
noise10 = tifffile.imread(subject_path + '10 Noise.tif')

phantom_mask = np.zeros_like(noiseless)
phantom_mask[noiseless > -900] = 1

# segment the air, assign that 0 and call everything else 1
air_mask = (phantom_mask == 0).astype(np.uint8)
labeled_volume, num_features = ndimage.label(air_mask)
print(f"Found {num_features} connected components")
component_sizes = ndimage.sum(air_mask, labeled_volume, range(1, num_features + 1))
component_sizes = np.array(component_sizes, dtype=np.int64)
largest_label = np.argmax(component_sizes) + 1
print(f"\nLargest air component is label {largest_label} "
      f"with {component_sizes[largest_label-1]:,} voxels")
phantom_mask[labeled_volume == largest_label] = 0
phantom_mask[labeled_volume != largest_label] = 1
tifffile.imwrite(subject_path + 'Phantom Mask.tif', phantom_mask)

# segment the lungs, create a mask
lung_mask = np.zeros_like(noiseless).astype(np.uint8)
junk_mask = np.zeros_like(noiseless).astype(np.uint8)
junk_mask[noiseless > -200] = 1
junk_mask2 = (junk_mask == 0)
lung_mask[(junk_mask2 > 0) & (phantom_mask > 0)] = 1
lung_mask = ndimage.binary_erosion(lung_mask, iterations=3)
lung_mask = ndimage.binary_dilation(lung_mask, iterations=6)
lung_mask = ndimage.binary_erosion(lung_mask, iterations=3) * 255
tifffile.imwrite(subject_path + 'Lung Mask.tif', lung_mask.astype(np.uint8))

# create a bone mask
bone_mask = np.zeros_like(noiseless).astype(np.uint8)
bone_mask[noiseless > 90] = 255
tifffile.imwrite(subject_path + 'Bone Mask.tif', bone_mask.astype(np.uint8))

# create a fat mask
fatty_mask = np.zeros_like(noiseless).astype(np.uint8)
fatty_mask[(noiseless > -50) & (noiseless < 90)] = 1
fatty_mask = ndimage.binary_erosion(fatty_mask, iterations=3)
fatty_mask = ndimage.binary_dilation(fatty_mask, iterations=3) * 255
tifffile.imwrite(subject_path + 'Fatty Mask.tif', fatty_mask.astype(np.uint8))

# create a water mask (just everything else basically)
watery_mask = np.zeros_like(noiseless).astype(np.uint8)
watery_mask[(phantom_mask > 0) & (lung_mask == 0) & (bone_mask == 0) & (fatty_mask == 0)] = 1
watery_mask = ndimage.binary_erosion(watery_mask, iterations=2)
watery_mask = ndimage.binary_dilation(watery_mask, iterations=2) * 255
tifffile.imwrite(subject_path + 'Watery Mask.tif', watery_mask.astype(np.uint8))

# do the standard deviation of the residual images on ImageJ
# I could have done this on Python, but this already exists on ImageJ and is significantly faster
'''
ImageJ Steps
1) open up noiseless and tcm
2) subtract noiseless from tcm to obtain noise only
3) compute standard deviation with block radius 5 -- save tif as {TCM} STD
'''

std00 = tifffile.imread(subject_path + '00 STD.tif')
std05 = tifffile.imread(subject_path + '05 STD.tif')
std10 = tifffile.imread(subject_path + '10 STD.tif')


def noise_profile(noiseless, std):
    depths = np.shape(noiseless)[0]
    rows = np.shape(noiseless)[1]
    columns = np.shape(noiseless)[2]
    axial = []
    coronal = []
    sagittal = []
    for i in range(depths):
        sheet = std[i, :, :]
        indices = np.where(sheet > 0)
        if len(indices[0]) == 0:
            axial.append(np.nan)
        else:
            axial.append(np.mean(sheet[indices]))
    for i in range(rows):
        sheet = std[:, i, :]
        indices = np.where(sheet > 0)
        if len(indices[0]) == 0:
            coronal.append(np.nan)
        else:
            coronal.append(np.mean(sheet[indices]))
    for i in range(columns):
        sheet = std[:, :, i]
        indices = np.where(sheet > 0)
        if len(indices[0]) == 0:
            sagittal.append(np.nan)
        else:
            sagittal.append(np.mean(sheet[indices]))
    return np.array(axial), np.array(coronal), np.array(sagittal)

def plot_segment(mask, noiseless, std00, std05, std10, seg_name, phantom_name):
    std00 = std00 * mask
    std05 = std05 * mask
    std10 = std10 * mask
    
    axial00, coronal00, sagittal00 = noise_profile(noiseless, std00)
    axial05, coronal05, sagittal05 = noise_profile(noiseless, std05)
    axial10, coronal10, sagittal10 = noise_profile(noiseless, std10)
    
    xaxial = np.arange(0, np.shape(noiseless)[0]) * 400/512
    xcoronal = np.arange(0, np.shape(noiseless)[1]) * 400/512
    xsagittal = np.arange(0, np.shape(noiseless)[2]) * 400/512
    
    if seg_name == 'Watery':
        colors = ['lawngreen', 'forestgreen', 'darkgreen']
    elif seg_name == 'Bone':
        colors = ['coral', 'red', 'firebrick']
    elif seg_name == 'Fatty':
        colors = ['orchid', 'mediumpurple', 'blueviolet']
    elif seg_name == 'Lung':
        colors = ['lightskyblue', 'dodgerblue', 'blue']
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), dpi=500)
    axes[0].plot(xaxial, axial00, label = r'$\alpha$ = 0.0', color=colors[0])
    axes[0].plot(xaxial, axial05, label = r'$\alpha$ = 0.5', color=colors[1])
    axes[0].plot(xaxial, axial10, label = r'$\alpha$ = 1.0', color=colors[2])
    axes[0].set_title(' ', fontsize=20)
    axes[0].set_xlabel('Distance Along Longitudinal Axis (mm)')
    axes[0].set_ylabel('Noise (HU)')
    axes[0].legend(loc='upper right')
    
    axes[1].plot(xcoronal, coronal00, label = r'$\alpha$ = 0.0', color=colors[0])
    axes[1].plot(xcoronal, coronal05, label = r'$\alpha$ = 0.5', color=colors[1])
    axes[1].plot(xcoronal, coronal10, label = r'$\alpha$ = 1.0', color=colors[2])
    axes[1].set_title(f'{phantom_name} ({seg_name})', fontsize=20)
    axes[1].set_xlabel('Distance Along Sagittal Axis (mm)')
    axes[1].set_ylabel('Noise (HU)')
    axes[1].legend(loc='upper right')
    
    axes[2].plot(xsagittal, sagittal00, label = r'$\alpha$ = 0.0', color=colors[0])
    axes[2].plot(xsagittal, sagittal05, label = r'$\alpha$ = 0.5', color=colors[1])
    axes[2].plot(xsagittal, sagittal10, label = r'$\alpha$ = 1.0', color=colors[2])
    axes[2].set_title(' ', fontsize=20)
    axes[2].set_xlabel('Distance Along Transverse Axis (mm)')
    axes[2].set_ylabel('Noise (HU)')
    axes[2].legend(loc='upper right')
    """
    plt.figure(figsize=(9, 4), dpi=500)
    plt.plot(xaxial, axial00, label = r'$\alpha$ = 0.0', color=colors[0])
    plt.plot(xaxial, axial05, label = r'$\alpha$ = 0.5', color=colors[1])
    plt.plot(xaxial, axial10, label = r'$\alpha$ = 1.0', color=colors[2])
    plt.title(f'F 25 BMI ({seg_name})', fontsize=20)
    plt.xlabel('Distance Along Longitudinal Axis (mm)')
    plt.ylabel('Noise (HU)')
    plt.legend(loc='upper right')
    """
    plt.tight_layout()
    plt.savefig(f'D:/CT TCM/Presentation Material/{phantom_name} {seg_name} Single.png')
    plt.show()

# plot noise along 3 axes for bone and lung
plot_segment(bone_mask / 255, noiseless, std00, std05, std10, 'Bone', phantom_name)
plot_segment(lung_mask / 255, noiseless, std00, std05, std10, 'Lung', phantom_name)

# quantify noise across the entire phantom for each segmentation
lung_noise = np.zeros(3)
bone_noise = np.zeros(3)
fat_noise = np.zeros(3)
water_noise = np.zeros(3)

lung_noise[0] = np.mean(std00[lung_mask > 0])
lung_noise[1] = np.mean(std05[lung_mask > 0])
lung_noise[2] = np.mean(std10[lung_mask > 0])

bone_noise[0] = np.mean(std00[bone_mask > 0])
bone_noise[1] = np.mean(std05[bone_mask > 0])
bone_noise[2] = np.mean(std10[bone_mask > 0])

fat_noise[0] = np.mean(std00[fatty_mask > 0])
fat_noise[1] = np.mean(std05[fatty_mask > 0])
fat_noise[2] = np.mean(std10[fatty_mask > 0])

water_noise[0] = np.mean(std00[watery_mask > 0])
water_noise[1] = np.mean(std05[watery_mask > 0])
water_noise[2] = np.mean(std10[watery_mask > 0])

plt.figure(figsize=(6,6), dpi=300)
x = np.array([0, 0.5, 1])
plt.plot(x, lung_noise, label = 'Lung', color = 'dodgerblue', marker='.', markersize=12)
plt.plot(x, bone_noise, label = 'Bone', color = 'red', marker='.', markersize=12)
plt.plot(x, fat_noise, label = 'Fatty Tissue', color = 'mediumpurple', marker='.', markersize=12)
plt.plot(x, water_noise, label = 'Watery Tissue', color = 'forestgreen', marker='.', markersize=12)
plt.xlabel(r'$\alpha$ Strength')
plt.ylabel('Noise Magnitude (HU)')
plt.ylim((12, 48))
plt.title(phantom_name, fontsize=16)
plt.legend()
plt.savefig(f'D:/CT TCM/Presentation Material/{phantom_name} Noise.png')
plt.show()