import os
import numpy as np
from PIL import Image
import tkinter as tk
from tkinter import filedialog

def grabChannel(image, channel):
    channels = {'R': 0, 'G': 1, 'B': 2, 'A': 3}
    if channel in channels and image.mode == 'RGBA':
        return image.split()[channels[channel]]
    elif channel in channels and image.mode == 'RGB':
        return image.split()[channels[channel]]
    elif channel == 'W':
        return Image.fromarray(np.full((image.size[1], image.size[0]), 255, dtype=np.uint8))
    else:
        raise ValueError(f"Unsupported channel: {channel}")

def processPBR(groupName, pbr, a_file=None, outputDir="Converted"):
    print("Found PBR texture: ", pbr)
    mTex = Image.open(pbr).convert('RGBA')
    r_channel = grabChannel(mTex, 'G')
    g_channel = grabChannel(mTex, 'B')
    b_channel = Image.fromarray(np.full((mTex.size[1], mTex.size[0]), 255, dtype=np.uint8))

    finalTex = Image.merge('RGB', (r_channel, g_channel, b_channel))
    finalTex.save(os.path.join(outputDir, f"{groupName}_S.tga"))

def processNormal(groupName, normal, pbr=None, outputDir="Converted"):
    print("Found Normal texture: ", normal)
    nTex = Image.open(normal).convert('RGBA')
    r_channel = grabChannel(nTex, 'R')
    g_channel = grabChannel(nTex, 'G')
    b_channel = grabChannel(nTex, 'W')

    if pbr:
        mTex = Image.open(pbr).convert('RGBA')
        mTexBlueChannel = grabChannel(mTex, 'B')
        if mTexBlueChannel.size != nTex.size:
            mTexBlueChannel = mTexBlueChannel.resize(nTex.size, Image.Resampling.LANCZOS)
        finalTex = Image.merge('RGBA', (r_channel, g_channel, b_channel, mTexBlueChannel))
    else:
        finalTex = Image.merge('RGB', (r_channel, g_channel, b_channel))

    finalTex.save(os.path.join(outputDir, f"{groupName}_N.tga"))

def processDiffuse(groupName, diffuse, outputDir="Converted"):
    print("Found Diffuse texture: ", diffuse)
    dTex = Image.open(diffuse).convert('RGBA')
    dTex.save(os.path.join(outputDir, f"{groupName}_D.tga"))

def generateVMT(groupName, chrName, fullBaseName, outputDir="Converted"):
    vmt_content = f'''"Patch"
{{
    include "materials/models/cpthazama/zzz/shared_common.vmt"
    replace
    {{
        "$basetexture"               "models/cpthazama/zzz/{chrName}/{fullBaseName}_D"
        "$phongexponenttexture"      "models/cpthazama/zzz/{chrName}/{fullBaseName}_S"
        "$bumpmap"                   "models/cpthazama/zzz/{chrName}/{fullBaseName}_N"
    }}
}}
'''
    vmt_file = os.path.join(outputDir, f"{groupName}.vmt")
    with open(vmt_file, 'w') as f:
        f.write(vmt_content)
    print(f"Generated VMT file: {vmt_file}")

def main():
    root = tk.Tk()
    root.withdraw()
    inputFolder = filedialog.askdirectory(title="Select Input Folder")

    if not inputFolder:
        print("No folder selected. Exiting.")
        return

    files = [f for f in os.listdir(inputFolder) if f.lower().endswith(('.png', '.tga'))]
    groups = {}
    outputDir = os.path.join(inputFolder, "Converted")
    lastGroup = None
    os.makedirs(outputDir, exist_ok=True)

    for f in files:
        nameBlocks = f.rsplit('_', 1)
        if len(nameBlocks) < 2:
            continue
        groupName = nameBlocks[0]
        identifier = nameBlocks[1].split('.')[0]
        if groupName not in groups:
            groups[groupName] = {}
        groups[groupName][identifier.upper()] = os.path.join(inputFolder, f)

    for groupName, fileDict in groups.items():
        if lastGroup != groupName:
            print("==========================================")
        lastGroup = groupName
        if 'M' not in fileDict and 'N' not in fileDict and 'D' not in fileDict:
            print(f"Skipping {groupName} as it doesn't meet the standard requirements.")
            continue
        print(f"Converting {groupName} textures...")

        nameBlocks = groupName.split('_')
        chrName = nameBlocks[0].lower()
        baseName = '_'.join(nameBlocks[1:])
        fullBaseName = f"{chrName.capitalize()}_{baseName}"

        if 'M' in fileDict:
            processPBR(groupName, fileDict['M'], fileDict.get('A'), outputDir)
        if 'N' in fileDict:
            processNormal(groupName, fileDict['N'], fileDict.get('M'), outputDir)
        if 'D' in fileDict:
            processDiffuse(groupName, fileDict['D'], outputDir)
        generateVMT(groupName, chrName, fullBaseName, outputDir)

if __name__ == "__main__":
    main()