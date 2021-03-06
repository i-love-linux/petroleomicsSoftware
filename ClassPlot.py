# coding=utf-8
# 此文件负责定义：负责画图
import matplotlib.pyplot as plt
import numpy as np
from Utils import *
from ConstValues import ConstValues


class ClassPlot:
    def __init__(self, parameterList, outputFilesPath):
        assert len(parameterList) == 17, "ClassPlot参数个数不对!"
        self.RemoveFPId = parameterList[0]  # 判断选择了哪一个文件：self.DelIsoResult 或者 self.PeakDisResult
        self.RemoveFPResult = parameterList[1]  # 所有类别去假阳性的结果，二维列表，有表头
        self.PlotTitleName = parameterList[2]  # 标题名称
        self.PlotTitleColor = parameterList[3]  # 标题颜色，(R, G, B, Alpha)，针对plt，值为0~255，需要转为0~1
        self.PlotXAxisName = parameterList[4]  # x轴名称
        self.PlotXAxisColor = parameterList[5]  # x轴颜色，(R, G, B, Alpha)，针对plt，值为0~255，需要转为0~1
        self.PlotYAxisName = parameterList[6]  # y轴名称
        self.PlotYAxisColor = parameterList[7]  # y轴颜色，(R, G, B, Alpha)，针对plt，值为0~255，需要转为0~1
        self.PlotHasEnter = parameterList[8]  # 记录是否进入过PlotSetup()函数
        self.PlotType = parameterList[9]  # 绘图类型
        self.PlotClassList = parameterList[10]  # 列表，需要绘制的类型，例子：["CH", "N1"]
        self.PlotClassItem = parameterList[11]  # 列表，需要绘制的类型，例子：["CH"]，对应单选钮，长度必须为1
        self.PlotDBENum = parameterList[12]  # 整数，记录用户选择的DBE数目
        self.PlotConfirm = parameterList[13]  # 是否需要绘图
        self.PlotAxisList = parameterList[14]  # 第七种类型图形绘制需要的数据，复选框选择的数据，为列表，x轴：N/C，y轴：H/C
        # 第六种图形去假阳性需要用户输入的内容
        self.PlotNeedRFP = parameterList[15]  # 是否需要根据图形绘制假阳性
        self.PlotMoveDistance = parameterList[16]  # 用户定义的平移的距离

        # 用户选择的文件的生成位置
        self.outputFilesPath = outputFilesPath

        # 去掉表头
        self.RemoveFPResult = self.RemoveFPResult[1:]

    # 主逻辑，画图
    def Plot(self):
        # 添加坐标名称，标题
        plt.xlabel(self.PlotXAxisName, fontproperties='SimHei', fontsize=12,
                   color=[num / 255 for num in self.PlotXAxisColor])
        plt.ylabel(self.PlotYAxisName, fontproperties='SimHei', fontsize=12,
                   color=[num / 255 for num in self.PlotYAxisColor])

        # 创建对应文件夹
        newDirectory = CreateDirectory(self.outputFilesPath, "./intermediateFiles", "/_7_plot")

        # 3.搜同位素 去假阳性后的数据
        # ["SampleMass", "SampleIntensity", "Class", "Neutral DBE", "Formula", "Calc m/z", "C", "ion"]
        ClassIndex = 2  # 类别对应的Index
        DBEIndex = 3  # 不饱和度对应的Index
        CIndex = 6  # C数对应的Index
        formulaIndex = 4  # formula数对应的Index
        if self.RemoveFPId == 2:  # 4.峰识别 去假阳性后的数据，需要加和的为area
            # ["SampleMass", "Area", "startRT", "startRTValue", "endRT", "endRTValue", "TICMassMedian",
            # "Class", "Neutral DBE", "Formula", "Calc m/z", "C", "ion"]
            ClassIndex = 7
            DBEIndex = 8
            CIndex = 11
            formulaIndex = 9
        sumIndex = 1  # 需要加和的为SampleIntensity，或者Area

        # 根据图的类型不同，绘制图形
        if self.PlotType == 1:  # Class distribution
            if len(self.PlotClassList) == 0:  # 不存在要绘制的类别，绘制失败
                plt.close()
                return None, []

            # 计算所需要的数据
            sumList = [0.0 for _ in range(len(self.PlotClassList))]
            # 转为字典，方便后面查找指定类型对应索引
            PlotClassDictionary = dict(zip(self.PlotClassList, [i for i in range(len(self.PlotClassList))]))
            for item in self.RemoveFPResult:
                if len(item) != 0:
                    if len(item) == 3:  # 搜同位素后去假阳性文件，还要跳过同位素
                        continue
                    itemClass = item[ClassIndex]
                    if itemClass in self.PlotClassList:
                        itemIndex = PlotClassDictionary[itemClass]  # 查询对应类别的下标
                        sumList[itemIndex] += item[sumIndex]
            sum = 0  # 计算总和
            for num in sumList:
                sum += num
            # 计算比例
            sumList = [num * 100 / sum for num in sumList]

            # 添加标题
            plt.title(self.PlotTitleName, fontproperties='SimHei', fontsize=12,
                      color=[num / 255 for num in self.PlotTitleColor])
            # 可以绘制图形，横坐标：self.PlotClassList，纵坐标：sumList
            plt.bar(self.PlotClassList, sumList)
            imagePath = newDirectory + "/" + self.PlotTitleName
            plt.savefig(fname=imagePath, dpi=150)
            # 关闭绘图
            plt.close()
            # 返回图片路径
            return imagePath + ".png", [[self.PlotXAxisName] + self.PlotClassList,
                                        [self.PlotYAxisName] + [num / 100 for num in sumList]]
        elif self.PlotType == 2:  # DBE distribution by class
            if len(self.PlotClassItem) == 0:  # 不存在要绘制的类别，绘制失败
                plt.close()
                return None, []

            # 计算所需要的数据
            DBEDictionary = {}  # key : DBE ,   value : 总量

            for item in self.RemoveFPResult:
                if len(item) != 0:
                    if len(item) == 3:  # 搜同位素后去假阳性文件，还要跳过同位素
                        continue
                    itemClass = item[ClassIndex]  # 获取类别
                    itemDBE = item[DBEIndex]  # DBE数目
                    if itemClass in self.PlotClassItem:
                        if itemDBE not in DBEDictionary:
                            DBEDictionary[itemDBE] = item[sumIndex]
                        else:
                            DBEDictionary[itemDBE] += item[sumIndex]

            # 提取出横纵坐标
            xList = []
            yList = []
            for key in sorted(DBEDictionary):
                value = DBEDictionary[key]
                xList.append(key)
                yList.append(value)

            sum = 0  # 计算总和
            for num in yList:
                sum += num
            yList = [num * 100 / sum for num in yList]  # 计算比例

            # 添加标题
            title = self.PlotTitleName + "_(" + str(self.PlotClassItem[0]) + ")"
            plt.title(title, fontproperties='SimHei', fontsize=12, color=[num / 255 for num in self.PlotTitleColor])
            # 可以绘制图形，横坐标：xList，纵坐标：yList
            plt.bar(xList, yList)
            imagePath = newDirectory + "/" + title
            plt.savefig(fname=imagePath, dpi=150)
            # 关闭绘图
            plt.close()
            # 返回图片路径
            return imagePath + ".png", [[self.PlotXAxisName] + xList,
                                        [self.PlotYAxisName] + [num / 100 for num in yList]]
        elif self.PlotType == 3:  # Carbon number distribution by class and DBE
            if (len(self.PlotClassItem) == 0) or (self.PlotDBENum == ConstValues.PsPlotDBENum):  # 不存在要绘制的类别，绘制失败
                plt.close()
                return None, []

            # 计算所需要的数据
            CDictionary = {}  # key : C ,   value : 总量

            for item in self.RemoveFPResult:
                if len(item) != 0:
                    if len(item) == 3:  # 搜同位素后去假阳性文件，还要跳过同位素
                        continue
                    itemClass = item[ClassIndex]  # 获取类别
                    itemDBE = item[DBEIndex]  # DBE数目
                    itemCNum = item[CIndex]
                    if (itemClass in self.PlotClassItem) and (self.PlotDBENum == itemDBE):
                        if itemCNum not in CDictionary:
                            CDictionary[itemCNum] = item[sumIndex]
                        else:
                            CDictionary[itemCNum] += item[sumIndex]

            # 提取出横纵坐标
            xList = []
            yList = []
            for key in sorted(CDictionary):
                value = CDictionary[key]
                xList.append(key)
                yList.append(value)

            sum = 0  # 计算总和
            for num in yList:
                sum += num

            yList = [num * 100 / sum for num in yList]  # 计算比例

            # 添加标题
            title = self.PlotTitleName + "_(" + str(self.PlotClassItem[0]) + "_DBE_" + str(self.PlotDBENum) + ")"
            plt.title(title, fontproperties='SimHei', fontsize=12, color=[num / 255 for num in self.PlotTitleColor])
            # 可以绘制图形，横坐标：xList，纵坐标：yList
            plt.bar(xList, yList)
            imagePath = newDirectory + "/" + title
            plt.savefig(fname=imagePath, dpi=150)
            # 关闭绘图
            plt.close()
            # 返回图片路径
            return imagePath + ".png", [[self.PlotXAxisName] + xList,
                                        [self.PlotYAxisName] + [num / 100 for num in yList]]
        elif self.PlotType == 4:  # DBE vs carbon number by class
            if len(self.PlotClassItem) == 0:  # 不存在要绘制的类别，绘制失败
                plt.close()
                return None, []

            # 计算所需要的数据
            DBECDictionary = {}  # key : (DBE, CNum),   value : 总量

            for item in self.RemoveFPResult:
                if len(item) != 0:
                    if len(item) == 3:  # 搜同位素后去假阳性文件，还要跳过同位素
                        continue
                    itemClass = item[ClassIndex]  # 获取类别
                    itemDBE = item[DBEIndex]  # DBE数目
                    itemCNum = item[CIndex]
                    if itemClass in self.PlotClassItem:  # 是需要绘制的类别
                        if (itemDBE, itemCNum) not in DBECDictionary:
                            DBECDictionary[(itemDBE, itemCNum)] = item[sumIndex]
                        else:
                            DBECDictionary[(itemDBE, itemCNum)] += item[sumIndex]

            # 提取出横纵坐标，气泡图的大小
            xList = []
            yList = []
            sizeList = []
            for key in sorted(DBECDictionary):
                value = DBECDictionary[key]
                xList.append(key[1])  # CNum
                yList.append(key[0])  # DBE
                sizeList.append(value)

            sum = 0  # 计算总和
            for num in sizeList:
                sum += num
            scaledSizeList = [num * 10000 / sum for num in sizeList]  # 计算比例

            # 添加标题
            title = self.PlotTitleName + "_(" + str(self.PlotClassItem[0]) + ")"
            plt.title(title, fontproperties='SimHei', fontsize=12, color=[num / 255 for num in self.PlotTitleColor])
            # 可以绘制图形，横坐标：xList，纵坐标：yList
            plt.scatter(xList, yList, s=scaledSizeList, c="red", alpha=0.6)
            imagePath = newDirectory + "/" + title
            plt.savefig(fname=imagePath, dpi=150)
            # 关闭绘图
            plt.close()
            # 返回图片路径
            return imagePath + ".png", [[self.PlotXAxisName] + xList, [self.PlotYAxisName] + yList, ["Size"] + sizeList]
        elif self.PlotType == 5:  # Kendrick mass defect （KMD）
            def round_up(num):
                # 默认num大于0，用round函数会造成数据错误，如：round(2.5) --> 2
                integer = int(num)
                decimalNum = num - integer
                if decimalNum >= 0.5:
                    return integer + 1
                else:
                    return integer

            sampleMassIndex = 0
            sampleMassSet = set()  # 记录不同的 sampleMass
            xList = []  # KM
            yList = []  # KMD
            for item in self.RemoveFPResult:
                if len(item) != 0:
                    if len(item) == 3:  # 搜同位素后去假阳性文件，还要跳过同位素
                        continue
                    # 获取sampleMass
                    sampleMass = item[sampleMassIndex]
                    # 记录数据
                    if sampleMass not in sampleMassSet:
                        KM = (sampleMass * 14.0) / 14.01565
                        NKM = round_up(KM)
                        KMD = NKM - KM
                        xList.append(NKM)
                        yList.append(KMD)
                    # 集合中添加元素
                    sampleMassSet.add(sampleMass)

            # 添加标题
            plt.title(self.PlotTitleName, fontproperties='SimHei', fontsize=12,
                      color=[num / 255 for num in self.PlotTitleColor])
            # 可以绘制图形，横坐标：xList，纵坐标：yList
            plt.scatter(xList, yList, s=20, c="blue", alpha=0.8)
            imagePath = newDirectory + "/" + self.PlotTitleName
            plt.savefig(fname=imagePath, dpi=150)
            # 关闭绘图
            plt.close()
            # 返回图片路径
            return imagePath + ".png", [[self.PlotXAxisName] + xList, [self.PlotYAxisName] + yList]
        elif self.PlotType == 6:  # Retention time vs carbon number
            if (len(self.PlotClassItem) == 0) or (self.PlotDBENum == ConstValues.PsPlotDBENum) or (
                    self.RemoveFPId == 1):  # 不存在要绘制的类别，绘制失败
                plt.close()
                return None, []

            # startRTValue 位置
            startRTValueIndex = 3
            # 计算所需要的数据
            xList = []  # CNum
            yList = []  # startRTValue

            for item in self.RemoveFPResult:
                if len(item) != 0:
                    if len(item) == 3:  # 搜同位素后去假阳性文件，还要跳过同位素
                        continue
                    itemClass = item[ClassIndex]  # 获取类别
                    itemDBE = item[DBEIndex]  # DBE数目
                    itemCNum = item[CIndex]  # C的数目
                    itemStartRTValue = item[startRTValueIndex]
                    if (itemClass in self.PlotClassItem) and (self.PlotDBENum == itemDBE):
                        xList.append(itemCNum)
                        yList.append(itemStartRTValue)

            # 添加标题
            title = self.PlotTitleName + "_(" + str(self.PlotClassItem[0]) + "_DBE_" + str(self.PlotDBENum) + ")"
            imagePath = newDirectory + "/" + title
            returnData = None
            if (not self.PlotNeedRFP) or (len(xList) <= 15):  # 不需要去假阳性 或者 点数目较少时直接存储
                plt.title(title, fontproperties='SimHei', fontsize=12, color=[num / 255 for num in self.PlotTitleColor])
                # 可以绘制图形，横坐标：xList，纵坐标：yList
                plt.scatter(xList, yList, s=20, c="blue", alpha=0.8)
                returnData = [[self.PlotXAxisName] + xList, [self.PlotYAxisName] + yList]
            else:  # 需要去假阳性
                splitXList = []  # 二维数组，[[x, ...], [...]]，分开是因为可能不连续
                splitYList = []
                coordinateList = []  # 二维数组，[[x1, x2], [y1, y2], ...]

                # 不连续的数据分割
                j = 0
                notContinueNum = 5
                while j < len(xList) - 1:
                    if not (xList[j] == xList[j + 1] or
                            (xList[j + 1] <= xList[j] + notContinueNum)):
                        break
                    j += 1
                if j == len(xList) - 1:  # 说明全部连续
                    splitXList.append(xList)
                    splitYList.append(yList)
                    # 求坐标
                    xMin = np.min(xList)
                    xMax = np.max(xList)
                    yMin = np.min(yList)
                    yMax = np.max(yList)
                    coordinateList.append([xMin, xMax])
                    coordinateList.append([yMin, yMax])
                else:  # 说明不是全部连续，需要分为两部分处理：[0...j]  [j+1...end]
                    # 第一段
                    splitXList.append(xList[:j + 1])
                    splitYList.append(yList[:j + 1])
                    xMin = np.min(xList[:j + 1])  # 求坐标
                    xMax = np.max(xList[:j + 1])
                    yMin = np.min(yList[:j + 1])
                    yMax = np.max(yList[:j + 1])
                    coordinateList.append([xMin, xMax])
                    coordinateList.append([yMin, yMax])
                    # 第二段
                    splitXList.append(xList[j + 1:])
                    splitYList.append(yList[j + 1:])
                    xMin = np.min(xList[j + 1:])  # 求坐标
                    xMax = np.max(xList[j + 1:])
                    yMin = np.min(yList[j + 1:])
                    yMax = np.max(yList[j + 1:])
                    coordinateList.append([xMin, xMax])
                    coordinateList.append([yMin, yMax])

                # 假阳性去除
                oneXList = []
                oneYList = []
                for j in range(len(splitXList)):  # 一幅图可能分为多个部分
                    deltaX = coordinateList[j * 2][1] - coordinateList[j * 2][0]
                    deltaY = coordinateList[j * 2 + 1][1] - coordinateList[j * 2 + 1][0]
                    if (deltaX == 0) or (deltaY == 0):  # 说明分割线水平或者垂直，直接保留全部数据
                        oneXList += splitXList[j]
                        oneYList += splitYList[j]
                        continue
                    xMin = coordinateList[j * 2][0]
                    yMin = coordinateList[j * 2 + 1][0]
                    for k in range(len(splitXList[j])):  # 依次考察各个点
                        x = splitXList[j][k]
                        y = splitYList[j][k]
                        # x * (yMax - yMin) - (y - moveDistance) * (xMax - xMin) - xMin * (yMax - yMin) + yMin * (xMax - xMin) > 0
                        if (x * deltaY - (y - self.PlotMoveDistance) * deltaX - xMin * deltaY + yMin * deltaX) >= 0:
                            oneXList.append(x)
                            oneYList.append(y)
                # 绘图
                plt.figure(figsize=(8, 4))
                plt.suptitle(title, fontproperties='SimHei', fontsize=12, color=[num / 255 for num in self.PlotTitleColor])
                plt.subplot2grid((1, 2), (0, 0))  # 左图，未除假阳性
                plt.title("去假阳性前", fontproperties='SimHei', fontsize=12)
                plt.xlabel(self.PlotXAxisName, fontproperties='SimHei', fontsize=12, color=[num / 255 for num in self.PlotXAxisColor])
                plt.ylabel(self.PlotYAxisName, fontproperties='SimHei', fontsize=12, color=[num / 255 for num in self.PlotYAxisColor])
                plt.scatter(xList, yList, s=10, c="blue", alpha=0.8)
                for j in range(int(len(coordinateList) / 2)):
                    plt.plot(coordinateList[j * 2], [Max + self.PlotMoveDistance for Max in coordinateList[j * 2 + 1]], ":", color="red")

                plt.subplot2grid((1, 2), (0, 1))  # 右图，去除假阳性
                plt.title("去假阳性后", fontproperties='SimHei', fontsize=12)
                plt.xlabel(self.PlotXAxisName, fontproperties='SimHei', fontsize=12, color=[num / 255 for num in self.PlotXAxisColor])
                # plt.ylabel(self.PlotYAxisName, fontproperties='SimHei', fontsize=12, color=[num / 255 for num in self.PlotYAxisColor])
                plt.scatter(oneXList, oneYList, s=10, c="blue", alpha=0.8)

                returnData = [
                    [self.PlotXAxisName] + xList + ["", "去假阳性后数据:", self.PlotXAxisName] + oneXList,
                    [self.PlotYAxisName] + yList + ["", "", self.PlotYAxisName] + oneYList
                ]
            # 保存图像
            plt.savefig(fname=imagePath, dpi=150)
            # 关闭绘图
            plt.close()
            # 返回图片路径
            return imagePath + ".png", returnData
            # # 为了考虑处理假阳性，生成数据：第1,3,5行...为x，2,4,6行...为y
            # return xList, yList
        elif self.PlotType == 7:  # van Krevelen by class
            if len(self.PlotClassList) == 0:  # 不存在要绘制的类别，绘制失败
                plt.close()
                return None, []

            # 检查绘图是否有意义，比如：self.PlotClassList = ["N1"]，横坐标为S/C，因为分子式中不存在S，因此无意义
            elementSet = set()
            for Class in self.PlotClassList:  # 获取某个类别，比如："N1S1"
                elementSet.clear()
                for element in Class:  # 获取某个字符，比如："N"
                    if not element.isdigit():
                        elementSet.add(element)
                for element in self.PlotAxisList:
                    if element == "C" or element == "H":
                        continue
                    if not (element in elementSet):
                        return None, []

            # 此时的数据一定有意义，计算绘图所需数据
            formulaDictionary = {}  # key : formula,   value : 总量

            for item in self.RemoveFPResult:
                if len(item) != 0:
                    if len(item) == 3:  # 搜同位素后去假阳性文件，还要跳过同位素
                        continue
                    itemClass = item[ClassIndex]  # 获取类别
                    itemFormula = item[formulaIndex]  # formula
                    if itemClass in self.PlotClassList:  # 是需要绘制的类别
                        if itemFormula not in formulaDictionary:
                            formulaDictionary[itemFormula] = item[sumIndex]
                        else:
                            formulaDictionary[itemFormula] += item[sumIndex]

            # 提取出横纵坐标，气泡图的大小
            formulaList = []
            xList = []
            yList = []
            sizeList = []
            for key in sorted(formulaDictionary):
                value = formulaDictionary[key]
                # 计算self.PlotAxisList中元素的个数
                elementDictionary = {}  # 格式：{"C":5, "H":14}
                i = 0
                while i < len(key):
                    j = i+1
                    while j < len(key):
                        if not key[j].isdigit():
                            break
                        j += 1
                    elementDictionary[key[i]] = key[i+1:j]
                    i = j
                xNumerator = int(elementDictionary[self.PlotAxisList[0]])  # x的分子
                xDenominator = int(elementDictionary[self.PlotAxisList[1]])  # x的分母
                yNumerator = int(elementDictionary[self.PlotAxisList[2]])  # y的分子
                yDenominator = int(elementDictionary[self.PlotAxisList[3]])  # y的分母
                xValue = 0
                if xNumerator > 0 and xDenominator > 0:
                    xValue = xNumerator / xDenominator
                yValue = 0
                if yNumerator > 0 and yDenominator > 0:
                    yValue = yNumerator / yDenominator
                formulaList.append(key)
                xList.append(xValue)
                yList.append(yValue)
                sizeList.append(value)

            sum = 0  # 计算总和
            for num in sizeList:
                sum += num
            scaledSizeList = [num * 10000 / sum for num in sizeList]  # 计算比例

            # 添加标题
            title = self.PlotTitleName + "_("
            for i in range(len(self.PlotClassList)):
                if i != len(self.PlotClassList) - 1:
                    title = title + str(self.PlotClassList[i]) + "_"
                else:
                    title = title + str(self.PlotClassList[i]) + ")"
            plt.title(title, fontproperties='SimHei', fontsize=12, color=[num / 255 for num in self.PlotTitleColor])
            # 可以绘制图形，横坐标：xList，纵坐标：yList
            plt.scatter(xList, yList, s=scaledSizeList, c="red", alpha=0.6)
            imagePath = newDirectory + "/" + title
            plt.savefig(fname=imagePath, dpi=150)
            # 关闭绘图
            plt.close()
            # 返回图片路径
            return imagePath + ".png", [["formula"] + formulaList, [self.PlotXAxisName] + xList, [self.PlotYAxisName] + yList, ["Size"] + sizeList]
