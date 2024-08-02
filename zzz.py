import os
import numpy as np
from PIL import Image

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

def processPBR(group_name, m_file, a_file=None, output_dir="Converted"):
    print("Found PBR texture: ", m_file)
    m_image = Image.open(m_file).convert('RGBA')

    r_channel = grabChannel(m_image, 'B')
    g_channel = grabChannel(m_image, 'G')

    b_channel = Image.fromarray(np.full((m_image.size[1], m_image.size[0]), 255, dtype=np.uint8))

    new_image = Image.merge('RGB', (r_channel, g_channel, b_channel))
    new_image.save(os.path.join(output_dir, f"{group_name}_S.tga"))

def processNormal(group_name, n_file, m_file=None, output_dir="Converted"):
    print("Found Normal texture: ", n_file)
    n_image = Image.open(n_file).convert('RGBA')
    r_channel = grabChannel(n_image, 'R')
    g_channel = grabChannel(n_image, 'G')
    b_channel = grabChannel(n_image, 'W')

    if m_file:
        m_image = Image.open(m_file).convert('RGBA')
        m_green_channel = grabChannel(m_image, 'G')
        new_image = Image.merge('RGBA', (r_channel, g_channel, b_channel, m_green_channel))
    else:
        new_image = Image.merge('RGB', (r_channel, g_channel, b_channel))

    new_image.save(os.path.join(output_dir, f"{group_name}_N.tga"))

def processDiffuse(group_name, d_file, output_dir="Converted"):
    print("Found Diffuse texture: ", d_file)
    d_image = Image.open(d_file).convert('RGBA')
    d_image.save(os.path.join(output_dir, f"{group_name}_D.tga"))

def generateVMT(group_name, char_name, full_base_name, output_dir="Converted"):
    vmt_content = f'''"VertexLitGeneric"
{{
    "$basetexture"               "models/cpthazama/zzz/{char_name}/{full_base_name}_D"
    "$detail"                    "models/cpthazama/zzz/{char_name}/{full_base_name}_D"
    "$phongexponenttexture"      "models/cpthazama/zzz/{char_name}/{full_base_name}_S"
    "$bumpmap"                   "models/cpthazama/zzz/{char_name}/{full_base_name}_N"

    "$color2"                    "[1.5 1.5 1.5]"
    "$nodecal"                   "1"
    "$nocull"                    "1"
    "$ambientocclusion"          "1"
    "$alphatest"                 "1"
    "$allowalphatocoverage"      "1"

    "$phong"                     "1"
    "$phongboost"                "10"
    "$phongfresnelranges"        "[0.1 0.356 0.525]"
    "$phongalbedotint"           "1"
    "$phongalbedoboost"          "50"

    "$normalmapalphaenvmapmask"  "1"
	"$envmapfresnel"             "1"
	"$envmap"                    "env_cubemap"
	"$envmaptint" 				 "[1 1 1]"

    "$rimlight"                  "1"
    "$rimlightexponent"          "5000"
    "$rimlightboost"             "2"

	"$DEM_TintScale" 			"[1 1 1]"
	"$DEM_Multiplier" 			"0.5"

    "Proxies" 
    {{
        "DynamicEnvMap"
        {{
            resultVar   "$envmaptint"
        }}
    }}

    "$lightwarptexture"          "models/cpthazama/zzz/shader"
}}
'''
    vmt_file = os.path.join(output_dir, f"{group_name}.vmt")
    with open(vmt_file, 'w') as f:
        f.write(vmt_content)
    print(f"Generated VMT file: {vmt_file}")

def main():
    files = [f for f in os.listdir() if f.lower().endswith(('.png', '.tga'))]
    groups = {}

    output_dir = "Converted"
    last_group = None
    os.makedirs(output_dir, exist_ok=True)

    for f in files:
        name_parts = f.rsplit('_', 1)
        if len(name_parts) < 2:
            continue
        group_name = name_parts[0]
        identifier = name_parts[1].split('.')[0]
        if group_name not in groups:
            groups[group_name] = {}
        groups[group_name][identifier.upper()] = f

    for group_name, file_dict in groups.items():
        if last_group != group_name:
            print("==========================================")
        last_group = group_name
        if 'M' not in file_dict and 'N' not in file_dict and 'D' not in file_dict:
            print(f"Skipping {group_name} as it doesn't meet the standard requirements.")
            continue
        print(f"Converting {group_name} textures...")
        
        parts = group_name.split('_')
        char_name = parts[0].lower()
        base_name = '_'.join(parts[1:])
        full_base_name = f"{char_name.capitalize()}_{base_name}"
        
        if 'M' in file_dict:
            processPBR(group_name, file_dict['M'], file_dict.get('A'), output_dir)
        if 'N' in file_dict:
            processNormal(group_name, file_dict['N'], file_dict.get('M'), output_dir)
        if 'D' in file_dict:
            processDiffuse(group_name, file_dict['D'], output_dir)
        generateVMT(group_name, char_name, full_base_name, output_dir)

if __name__ == "__main__":
    main()
