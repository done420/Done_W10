import extcolors
import os,cv2,PIL
import webcolors,json
import numpy as np
from scipy.spatial import KDTree
import matplotlib.pyplot as plt
from collections import Counter
import numpy


### 读取居其家居颜色信息表
file = open("./ColourIndex.json", "r")
DICT = json.load(file)
file.close()

colorname2rgb = [(ele["name_cn"], ele["rgb_value"]) for K, V in DICT.items() for ele in V['color_data']]

Colorname2RGB = dict([ele[0], tuple(ele[1])] for ele in colorname2rgb)

color2collocation = [(ele["name_cn"], K) for K, V in DICT.items() for ele in V['color_data']]
Color2Collocation = dict([ele[0], ele[1]] for ele in color2collocation)

WEB_DICT = webcolors.css3_hex_to_names  # webcolors.CSS3_HEX_TO_NAMES

COLOR_COLLOCATION = {
	'BlueSeries': '蓝色系',
	'BrownSeries': '棕色系',
	'GraySeries': '灰色系',
	'GreenSeries': '绿色系',
	'OrangeSeries': '橙色系',
	'PinkSeries': '粉色系',
	'PurpleSeries': '紫色系',
	'RedSeries': '红色系',
	'YellowSeries': '黄色系'
}


def dict_index(dict_to_use):
	names, colors = [], []
	if dict_to_use == WEB_DICT:
		for wb_hex, wb_name in dict_to_use.items():
			names.append(wb_name)
			colors.append(webcolors.hex_to_rgb(wb_hex))
	# print(wb_hex)
	else:
		for name, color in dict_to_use.items():
			names.append(name)
			colors.append(color)

	return names, colors


CN_NAMES, CN_COLOURS = dict_index(Colorname2RGB)
EN_NAMES, EN_COLOURS = dict_index(WEB_DICT)
print(EN_COLOURS)
CN_SPACEDB = KDTree(CN_COLOURS)
WB_SPACEDB = KDTree(EN_COLOURS)


print(CN_NAMES)
print(CN_COLOURS)

def colour_name_mapping(requested_rgb_colour):
	#### 居其家居颜色匹配，获取中文名称
	cn_dist, cn_index = CN_SPACEDB.query(requested_rgb_colour)
	closest_cn_name = CN_NAMES[cn_index]
	closest_cn_rgb = CN_COLOURS[cn_index]  ### 匹配后的最邻近rgb颜色
	closest_rgb = closest_cn_rgb  #### 将匹配到的居其家居最邻近颜色映射到webcolors，获取颜色英文名称

	#### 获取颜色英文名称
	try:
		closest_en_name = webcolors.rgb_to_name(closest_rgb)
	except ValueError:
		wb_dist, wb_index = WB_SPACEDB.query(closest_rgb)
		closest_en_name = EN_NAMES[wb_index]
	# closest_wb_rgb = EN_COLOURS[wb_index]

	return closest_en_name, closest_cn_name, closest_rgb, cn_dist  ### 返回最邻近颜色英文名称，最邻近颜色中文名称（居其家居），最邻近颜色rgb及距离

def RGB2HEX(color):  ##### 颜色转化
	return "#{:02x}{:02x}{:02x}".format(int(color[0]), int(color[1]), int(color[2]))

def image_extcolor(imgFile, k=5):

	colors, pixel_count = extcolors.extract_from_path(imgFile)

	def RGB2HEX(color):  ##### 颜色转化
		return "#{:02x}{:02x}{:02x}".format(int(color[0]), int(color[1]), int(color[2]))

	sorted_hex = [RGB2HEX(ele[0]) for ele in colors]
	sorted_counts = [(i, ele[1]) for i, ele in enumerate(colors)]
	sorted_rgb = [ele[0] for i, ele in enumerate(colors)]
	sorted_names = [(colour_name_mapping(i)[:2]) for i in sorted_rgb]
	rgb_percentage = [(ele[1] / pixel_count) for ele in sorted_counts]
	cluster_collocation = [Color2Collocation[ele[-1]] for ele in sorted_names]  ### 颜色色系，映射到居其家居
	cluster_collocation = [(i, COLOR_COLLOCATION[i]) for i in cluster_collocation]

	Result = {
		"k": k if len(colors) >= k else len(colors),
		"sorted_counts": sorted_counts[:k] if len(colors) > k else sorted_counts,
		"sorted_rgb": sorted_rgb[:k] if len(colors) > k else sorted_rgb,
		"sorted_hex": sorted_hex[:k] if len(colors) > k else sorted_hex,
		"sorted_names": sorted_names[:k] if len(colors) > k else sorted_names,
		"rgb_percentage": rgb_percentage[:k] if len(colors) > k else rgb_percentage,
		"color_collocation": cluster_collocation[:k] if len(colors) > k else cluster_collocation
	}

	return Result,colors


def simple_warm_cold_color(colors):
	warm_colors = []
	cold_colors = []

	for c in colors:
		r, g, b = c[0]
		if b > r:
			color = 'cold'
			cold_colors.append(c)

		else:
			color = 'warm'
			warm_colors.append(c)

	warm_colors_sorted = sorted(warm_colors, key=lambda x: x[1], reverse=True)
	cold_colors_sorted = sorted(cold_colors, key=lambda x: x[1], reverse=True)
	warm_index = [colors.index(ele) for ele in warm_colors_sorted if ele in colors]
	cold_inde = [colors.index(ele) for ele in cold_colors_sorted if ele in colors]
	print("warm_index:", warm_index)
	print("cold_inde:", cold_inde)

	return warm_colors_sorted, cold_colors_sorted


def view_image_color(extcolor_colors, size):
	import math
	from PIL import Image, ImageDraw
	columns = 5
	width = int(min(len(extcolor_colors), columns) * size)
	height = int((math.floor(len(extcolor_colors) / columns) + 1) * size)

	result = Image.new("RGBA", (width, height), (0, 0, 0, 0))
	canvas = ImageDraw.Draw(result)
	for idx, color in enumerate(extcolor_colors):
		x = int((idx % columns) * size)
		y = int(math.floor(idx / columns) * size)
		canvas.rectangle([(x, y), (x + size - 1, y + size - 1)],fill=color[0])

	plt.imshow(result),plt.axis('off')
	plt.show()


def view_hex_color(hex_colorList):
	import seaborn as sns
	import matplotlib.pyplot as plt

	sns.palplot(sns.color_palette(hex_colorList))
	plt.axis('off')
	plt.show()



def result_view(extcolor_colors,imgFile):
	def view_image_color(extcolor_colors, size=10):
		import math
		from PIL import Image, ImageDraw
		columns = 5
		width = int(min(len(extcolor_colors), columns) * size)
		height = int((math.floor(len(extcolor_colors) / columns) + 1) * size)

		result = Image.new("RGBA", (width, height), (0, 0, 0, 0))
		canvas = ImageDraw.Draw(result)
		for idx, color in enumerate(extcolor_colors):
			x = int((idx % columns) * size)
			y = int(math.floor(idx / columns) * size)
			canvas.rectangle([(x, y), (x + size - 1, y + size - 1)], fill=color[0])

		return result

	image = cv2.imread(imgFile)
	image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
	w,h,c = image.shape
	plt.subplot(2, 1, 1)
	plt.imshow(image)
	plt.subplot(2, 1, 2)

	# color_extract = view_image_color(extcolor_colors, size=10)
	color_extract = view_image_color(extcolor_colors, size=100)
	plt.imshow(color_extract)
	plt.show()





def result_view2(extcolor_colors, imgFile, is_save=False):
	def view_image_color(extcolor_colors, size=10):
		import math
		from PIL import Image, ImageDraw
		columns = 5
		width = int(min(len(extcolor_colors), columns) * size)
		height = int((math.floor(len(extcolor_colors) / columns) + 1) * size)

		result = Image.new("RGBA", (width, height), (0, 0, 0, 0))
		canvas = ImageDraw.Draw(result)
		for idx, color in enumerate(extcolor_colors):
			x = int((idx % columns) * size)
			y = int(math.floor(idx / columns) * size)
			canvas.rectangle([(x, y), (x + size - 1, y + size - 1)], fill=color[0])

		return result

	image = cv2.imread(imgFile)
	image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
	plt.subplot(4, 1, 1)
	plt.imshow(image),plt.axis('off')

	plt.subplot(4, 1, 2)
	color_extract = view_image_color(extcolor_colors, size=10)
	plt.imshow(color_extract),plt.axis('off')

	warm_colors, cold_colors = simple_warm_cold_color(extcolor_colors)

	plt.subplot(4, 1, 3)
	if warm_colors:
		warm_plate = view_image_color(warm_colors, size=2)
		# mg = cv2.cvtColor(numpy.asarray(warm_plate), cv2.COLOR_RGB2BGR)
		# cv2.imshow("cold_plate", mg)
		# cv2.waitKey(0)

		plt.imshow(warm_plate),plt.axis('off')

	plt.subplot(4, 1, 4)
	if cold_colors:
		cold_plate = view_image_color(cold_colors, size=2)
		# mg = cv2.cvtColor(numpy.asarray(cold_plate), cv2.COLOR_RGB2BGR)
		# cv2.imshow("cold_plate",mg)
		# cv2.waitKey(0)

		plt.imshow(cold_plate),plt.axis('off')

	if is_save:
		save_dir = r'.\test_in\save_out'
		save_file = os.path.join(save_dir,os.path.basename(imgFile))
		plt.savefig(save_file)


	plt.show()
	plt.close()




# # imgFile = "201811161542361479066046833.jpg"
# # imgFile = '201812061544080252425074770.jpg'
# imgFile = '201709041504488672469032117.jpg'
# img = cv2.imread(imgFile)
# img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
#
# result,colors = image_extcolor(imgFile)
# hex_colors = result['sorted_hex']
# num_color = result['k']
#
# # print(colors)
# # # view_image_color(colors[:num_color],150)
# # # view_hex_color(hex_colors)
# # extract_color = colors[:num_color]
# # result_view(extract_color,imgFile)
# # # print(extract_color)
# # # result_view2(colors,imgFile,False)




