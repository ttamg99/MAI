import arcpy
original_land = "ori2000.shp"
new_land = "2005-2000.shp"
arcpy.env.workspace = "C:\ArcGIS_Download\HF_MAI\m2005_2000"

buffer_distance = 30             # 缓冲区的距离间隔
num_buffers = 5                  # 缓冲区的数量, 同时生成的多个缓冲区序号是否对应
buffers = []
buffers.append(new_land)     # 把new_land作为buffers[0]
for i in range(num_buffers):
    buffer_layer = "buffer_raw_{}".format(i)
    arcpy.Buffer_analysis(new_land, buffer_layer, buffer_distance * (i + 1))    # 在新增斑块上生成缓冲区，不过生成的缓冲区是乱序的，需正确排序
    arcpy.Sort_management("C:\\ArcGIS_Download\\HF_MAI\\m2005_2000\\buffer_raw_{}.shp".format(i), "C:\\ArcGIS_Download\\HF_MAI\\m2005_2000\\buffer_{}.shp".format(i), "ID ASCENDING")
    buffer_order_layer = "C:\\ArcGIS_Download\\HF_MAI\\m2005_2000\\buffer_{}.shp".format(i)
    buffers.append(buffer_order_layer)              # 正确排序后的缓冲区

#  第一层缓冲区的MAI计算，需要直接生成，后续则直接更新

output = "MAI.shp"
if not arcpy.Exists(output):
    arcpy.CreateFeatureclass_management(arcpy.env.workspace, "MAI.shp", "POLYGON")
buffer_current = buffers[1]
arcpy.AddField_management(output, "MAI", "DOUBLE")        # 增加MAI指标的部分
with arcpy.da.SearchCursor(buffer_current, ["SHAPE@", "SHAPE@AREA", "ID"]) as buffer_cursor:      # 得到所有的缓冲块
    with arcpy.da.SearchCursor(new_land, ["SHAPE@", "SHAPE@AREA", "ID"]) as new_cursor:
        for row1, row2 in zip(buffer_cursor, new_cursor):
            buffer = row1[0]                # 得到形状信息
            idx = row1[2]                   # 得到序号，使得后续的MAI也有对应斑块的序号，help后续可视化
            area1 = row2[1]
            area2 = row1[1]
            buffer_area = area2 - area1    # 生成的缓冲区面积包含了原来新增斑块的面积，需要减掉
            intersect_area = 0        # 相交的面积，每一个缓冲区块计算时初始化为0       
            with arcpy.da.SearchCursor(original_land, ["SHAPE@"]) as ori_cursor:
                for ori_row in ori_cursor:
                    ori = ori_row[0]
                    if ori.overlaps(buffer):
                        intersect = ori.intersect(buffer, 4)      # 当前buffer与某一个斑块的交叉面积
                        intersect_area += intersect.area          # 得到当前缓冲区块与所有原有斑块的相交面积
            mai = 1 - intersect_area / buffer_area     # 当前缓冲区块的mai值
            temp = arcpy.da.InsertCursor(output, ["SHAPE@", "Id", "MAI"])
            feature = [buffer, idx, mai]
            temp.insertRow(feature)
            del temp



for i in range(2, num_buffers + 1):
    buffer_current = buffers[i]
    buffer_before = buffers[i-1]
    with arcpy.da.SearchCursor(buffer_current, ["SHAPE@", "SHAPE@AREA", "ID"]) as buffer_cursor:      # 得到所有的缓冲块
        with arcpy.da.SearchCursor(buffer_before, ["SHAPE@", "SHAPE@AREA", "ID"]) as new_cursor:
            for row1, row2 in zip(buffer_cursor, new_cursor):
                buffer = row1[0]                # 得到形状信息
                idx = row1[2]                   # 得到序号，使得后续的MAI也有对应斑块的序号，help后续可视化
                area1 = row2[1]
                area2 = row1[1]
                buffer_area = area2 - area1    # 生成的缓冲区面积包含了原来新增斑块的面积，需要减掉
                intersect_area = 0        # 相交的面积，每一个缓冲区块计算时初始化为0
                with arcpy.da.SearchCursor(original_land, ["SHAPE@"]) as ori_cursor:
                    for ori_row in ori_cursor:
                        ori = ori_row[0]
                        if ori.overlaps(buffer):
                            intersect = ori.intersect(buffer, 4)      # 当前buffer与某一个斑块的交叉面积
                            intersect_area += intersect.area          # 得到当前缓冲区块与所有原有斑块的相交面积
                mai = i - intersect_area / buffer_area     # 当前缓冲区块的mai值
                with arcpy.da.UpdateCursor(output, ["MAI"], "ID = {}".format(idx)) as cursor:    #  判断当前序号的MAI值是否需要更新
                    for row in cursor:
                        old_mai = row[0]
                        if old_mai == i -1:           #  说明上一层缓冲区没有相交的部分，需要更新
                            row[0] = mai    
                            cursor.updateRow(row)








