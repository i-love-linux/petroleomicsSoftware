# coding=utf-8
# 此文件负责定义：峰识别（第一阶段）
# 第二部分是 峰检测：检测出各个峰，并计算面积
import numpy as np
from Utils import *
from ConstValues import ConstValues
import sys


class ClassPeakDistinguish:
    def __init__(self, parameterList, outputFilesPath):
        assert len(parameterList) == 7, "ClassPeakDistinguish参数个数不对!"
        # self.TICData是读入后并处理后的数据, 为字典：{key: value}，value为二维列表[[Mass, Intensity], ..., [Mass, Intensity]]
        self.TICData = parameterList[0]  # 总离子流图路径（第一阶段）
        self.DelIsoResult = parameterList[1]  # 扣同位素后生成的文件，两项记录之间通过空列表分割（格式：list二维数组，有表头）
        self.PeakDisContinuityNum = parameterList[2]  # 连续出现的扫描点个数，格式：整数
        self.PeakDisMassDeviation = parameterList[3]  # 质量偏差，格式：浮点数
        self.PeakDisDiscontinuityPointNum = parameterList[4]
        self.PeakDisClassIsNeed = parameterList[5]  # 第二部分，峰检测分割
        self.PeakDisClass = parameterList[6]
        # 第一部分结果
        self.resultPart1 = None
        self.resultPart1Detail = None
        # 用户选择的文件的生成位置
        self.outputFilesPath = outputFilesPath

    # 负责峰识别
    def PeakDistinguish(self):
        # 获取排序后的RT，后面峰检测需要使用
        sortedRTValue = sorted([float(num) for num in list(self.TICData)])
        newDirectory = CreateDirectory(self.outputFilesPath, "./intermediateFiles", "/_4_peakDistinguish")
        WriteDataToExcel([sortedRTValue], newDirectory + "/sortedRTValue.xlsx")  # 只有一行，没有表头，峰检测（第二部分）需要
        # 去掉表头
        self.DelIsoResult = self.DelIsoResult[1:]
        # 说明读取的文件存在问题
        if self.TICData is None:
            return [], False
        self.resultPart1 = []  # 第一部分，识别连续的扫描点
        headerPart1 = ["SampleMass", "Area", "startRT", "startRTValue", "endRT", "endRTValue", "TICMassMedian", "Class", "Neutral DBE", "Formula", "Calc m/z", "C", "ion"]
        self.resultPart1.append(headerPart1)
        # 存储第一阶段的详细信息，为第二阶段做准备，三维列表[[a, ..., b], ...]
        # self.resultPart1Detail[0]代表某个去同位素后的样本在TIC中的所有数据（如果连续或没匹配上为0）。
        # self.resultPart1Detail[0]前面部分为该样本的信息，字段和  类型一 一样
        # self.resultPart1Detail中所有的数据都是是用户输入的需要进行峰检测（第二部分）的类别
        self.resultPart1Detail = []
        flag = 1
        runTime = 0

        for sampleItem in self.DelIsoResult:
            # sampleItem均为列表，有多种类型：
            # 类型一：["SampleMass", "SampleIntensity", "Class", "Neutral DBE", "Formula", "Calc m/z", "C", "ion"]
            # 类型二：["SampleMass", "SampleIntensity"]
            # 类型三：[DBItem_13C1, DBItem_13C1Intensity, "iostope"]或者[DBItem_13C2, DBItem_13C2Intensity, "iostope"]
            # 类型四：[]
            if len(sampleItem) == 8:
                ret, retDetail = self.PeakDisHandleItem(sampleItem)
                # 结果数据显示
                for item in ret:
                    self.resultPart1.append(item)
                # 峰检测过程使用的数据
                if len(retDetail) != 0:
                    self.resultPart1Detail.append(sampleItem + [":"] + retDetail)
                # 运行过程中调试输出信息
                runTime += 1
                if ConstValues.PsIsDebug and runTime % 100 == 0:
                    print("程序正在运行... runTime:", runTime)

        if ConstValues.PsIsDebug:
            print(
                "***Debug In \"", self.__class__.__name__, "\" class，In \"",
                sys._getframe().f_code.co_name, "\" method***：",
                "Finished!"
            )
        # 峰识别按照Formula（主键），C（次主键）从小到大顺序排序
        self.resultPart1 = self.PeakDisSort()
        self.resultPart1Detail = self.PeakDisSortDetail()

        # 数据写入excel文件中
        WriteDataToExcel(self.resultPart1, newDirectory + "/" + ConstValues.PsNamePeakDistinguish)
        WriteDataToExcel(self.resultPart1Detail, newDirectory + "/PeakDisPart1DetailPlot.xlsx")

        # # 为了录屏演示用，直接从文件读取
        # self.resultPart1 = ReadExcelToList("./intermediateFiles/_4_peakDistinguish/" + ConstValues.PsNamePeakDistinguish)
        # self.resultPart1Detail = ReadExcelToList("./intermediateFiles/_4_peakDistinguish/PeakDisPart1DetailPlot.xlsx", hasNan=False)
        # sortedRTValue = ReadExcelToList("./intermediateFiles/_4_peakDistinguish/sortedRTValue.xlsx", hasNan=False)[0]

        return [self.resultPart1, self.resultPart1Detail, sortedRTValue], True

    # 负责判断某个扣同位素后的样本是否能成功在总离子流图文件(txt)查到符合条件的记录集合
    def PeakDisHandleItem(self, sampleItem):
        # 获取样本中的Mass（Mass0）
        sampleMass = sampleItem[0]
        # # 获取样本的类型，判断是否需要进行第二部分
        needDetectPeak = False
        if (sampleItem[2] in self.PeakDisClass) and self.PeakDisClassIsNeed:
            needDetectPeak = True
        # 获取字典的长度
        scanNum = len(self.TICData)
        # 将字典的键转化为列表
        keysList = list(self.TICData)
        ret = []
        retDetail = []  # 第二部分信息

        k = 0
        while k < scanNum:
            firstRT = None
            continuityItems = []  # 存储连续的符合要求的记录，为二维列表[[Mass, Intensity],...,[Mass, Intensity]]
            continuityItems2 = []
            while k < scanNum and firstRT is None:
                firstRT = self.PeakDisHasCorrespondInTIC(keysList, sampleMass, k)
                if needDetectPeak:
                    if (firstRT is None) or (k == scanNum - 1):
                        retDetail.append(0)
                    else:
                        retDetail.append(firstRT[1])
                k += 1
            if k >= scanNum:
                break
            # 此时保证在self.TICData找到第一个符合要求的记录
            startRT = k - 1
            continuityItems.append(firstRT)  # 不严格连续，同时不连续的条目记为[0,0]
            continuityItems2.append(firstRT)  # 不严格连续，不记录不连续的条目，为了计算中位数
            # 寻找连续的符合要求的记录
            DiscontinuityPointNum = 0
            nextRT = self.PeakDisHasCorrespondInTIC(keysList, sampleMass, k)
            if nextRT is None:
                DiscontinuityPointNum += 1
            while k < scanNum and ((nextRT is not None) or DiscontinuityPointNum < self.PeakDisDiscontinuityPointNum):
                if nextRT is None:
                    DiscontinuityPointNum += 1
                    continuityItems.append([0, 0])
                    if needDetectPeak:
                        retDetail.append(0)
                else:
                    DiscontinuityPointNum = 0
                    continuityItems.append(nextRT)
                    continuityItems2.append(nextRT)
                    if needDetectPeak:
                        retDetail.append(nextRT[1])
                k += 1
                if k >= scanNum:
                    break
                nextRT = self.PeakDisHasCorrespondInTIC(keysList, sampleMass, k)
            if needDetectPeak and k < scanNum:  # 因为跳出上面的循环说明此时nextRT不符合要求
                retDetail.append(0)
            # 到这里连续的记录已经结束
            if len(continuityItems) >= self.PeakDisContinuityNum:  # 说明连续的扫描点数目符合要求
                continuityItems = np.array(continuityItems)
                continuityItems2 = np.array(continuityItems2)
                continuityMasses2 = continuityItems2[:, 0]
                continuityIntensities = continuityItems2[:, 1]

                Area = np.sum(continuityIntensities)  # 求面积
                startRTValue = keysList[startRT]  # 开始的扫描点的值
                endRT = startRT + len(continuityItems) - 1  # 结束的扫描点在TIC中属于第几个扫描点
                endRTValue = keysList[endRT]  # 结束的扫描点的值

                # 计算中位数：应该是先计算最大值，然后各个intensity／最大值，选取大于最大值60%的 m/z，取中位数
                thresholdValue = np.max(continuityIntensities) * 0.1
                greaterThanThresholdList = []
                for i in range(len(continuityMasses2)):
                    mass = continuityMasses2[i]
                    value = continuityIntensities[i]
                    if value > thresholdValue:
                        greaterThanThresholdList.append(mass)
                MassMedian = -1  # 代表不存在这样的中位数，理论上一定存在
                if len(greaterThanThresholdList) > 0:
                    MassMedian = np.median(np.array(greaterThanThresholdList))  # TIC中所有符合条件的连续的记录的

                ret.append([sampleMass, Area, startRT, startRTValue, endRT, endRTValue, MassMedian] + sampleItem[2:])
            elif needDetectPeak:  # 需要将连续的但扫描点数目不符合要求的数据值清零
                length1 = len(retDetail)
                length2 = len(continuityItems)
                if k < scanNum:  # 说明还没到最后，但是连续的扫描点数目不符合要求
                    for i in range(length1 - length2 - 1, length1 - 1):
                        retDetail[i] = 0
                else:  # 说明最后的数据都符合要求，但是连续的扫描点数目不符合要求
                    for i in range(length1 - length2, length1):
                        retDetail[i] = 0
            # 本次连续的考察完毕，进行之后没有考虑的扫描点考察
            k += 1
        if len(ret) != 0:
            ret.append([])
        return ret, retDetail

    # 搜索RTk中是否存在和sampleMass相近的记录
    def PeakDisHasCorrespondInTIC(self, keysList, sampleMass, k):
        value = self.TICData[keysList[k]]  # value为二维列表[[Mass, Intensity],...,[Mass, Intensity]]
        for item in value:
            TICMass = item[0]
            # TICIntensity = item[1]
            if abs((TICMass - sampleMass) * 1000000.0 / sampleMass) < self.PeakDisMassDeviation:
                return item
        return None

    # 峰识别按照Formula（主键），C（次主键）从小到大顺序排序
    def PeakDisSort(self):
        # self.PeakDisResult
        # ["SampleMass", "Area", "startRT", "startRTValue", "endRT", "endRTValue", "TICMassMedian", "Class", "Neutral DBE", "Formula", "Calc m/z", "C", "ion"]
        # {key:[ [...], ..., [...]] , ..., [[...], ..., [...]]], ..., key:[...]}，[[...], ..., [...]]对应某个分子式，[...]长度为13
        dataDirectory = {}  # 记录所有符合要求的数据
        # {key:[ [...] , ..., [...] ], ..., key:[ [...] , ..., [...] ]}，[...]对应某个分子式，长度为8
        dataOneDirectory = {}  # 某个分子式对应多条记录，只记录第一条，长度为3，最后一个数据记录其位置

        # 以类别为键，将数据整理为字典
        i = 1  # 跳过表头
        length = len(self.resultPart1)
        while i < length:
            firstItem = self.resultPart1[i]
            item = [firstItem]  # 是一个二维列表，对应一种物质
            i += 1
            if i < length:
                nextItem = self.resultPart1[i]
                while len(nextItem) != 0:
                    item.append(nextItem)
                    i += 1
                    if i >= length:
                        break
                    nextItem = self.resultPart1[i]

            key = firstItem[7]  # "Class"作为键
            if key in dataDirectory.keys():
                dataDirectory[key].append(item)
                dataOneDirectory[key].append([firstItem[8]] + [firstItem[11]] + [len(dataOneDirectory[key])])
            else:
                dataDirectory[key] = [item]
                dataOneDirectory[key] = [[firstItem[8]] + [firstItem[11]] + [0]]
            # 查看下一条数据
            i += 1

        # 对dataOneDirectory中的各项进行排序
        for key in dataOneDirectory.keys():
            dataOneDirectory[key] = sorted(dataOneDirectory[key], key=(lambda x: [x[0], x[1]]), reverse=False)

        # 重新整理结果
        ret = [["SampleMass", "Area", "startRT", "startRTValue", "endRT", "endRTValue", "TICMassMedian", "Class",
                "Neutral DBE", "Formula", "Calc m/z", "C", "ion"]]
        for key in dataOneDirectory.keys():
            data = dataOneDirectory[key]
            for item1 in data:
                for item2 in dataDirectory[key][item1[2]]:
                    ret.append(item2)
                ret.append([])
        return ret

    # 峰识别按照Formula（主键），C（次主键）从小到大顺序排序
    def PeakDisSortDetail(self):
        # self.PeakDisResult
        # ["SampleMass", "Area", "startRT", "startRTValue", "endRT", "endRTValue", "TICMassMedian", "Class", "Neutral DBE", "Formula", "Calc m/z", "C", "ion"]
        # {key:[ [...], ..., [...]] , ..., [[...], ..., [...]]], ..., key:[...]}，[[...], ..., [...]]对应某个分子式，[...]长度为13
        dataDirectory = {}  # 记录所有符合要求的数据
        # {key:[ [...] , ..., [...] ], ..., key:[ [...] , ..., [...] ]}，[...]对应某个分子式，长度为8
        dataOneDirectory = {}  # 某个分子式对应多条记录，只记录第一条，长度为3，最后一个数据记录其位置

        # 以类别为键，将数据整理为字典
        i = 1  # 跳过表头
        length = len(self.resultPart1Detail)
        while i < length:
            firstItem = self.resultPart1Detail[i]
            item = [firstItem]  # 是一个二维列表，对应一种物质
            i += 1
            if i < length:
                nextItem = self.resultPart1Detail[i]
                while len(nextItem) != 0:
                    item.append(nextItem)
                    i += 1
                    if i >= length:
                        break
                    nextItem = self.resultPart1Detail[i]

            key = firstItem[7]  # "Class"作为键
            if key in dataDirectory.keys():
                dataDirectory[key].append(item)
                dataOneDirectory[key].append([firstItem[3]] + [firstItem[6]] + [len(dataOneDirectory[key])])
            else:
                dataDirectory[key] = [item]
                dataOneDirectory[key] = [[firstItem[3]] + [firstItem[6]] + [0]]
            # 查看下一条数据
            i += 1

        # 对dataOneDirectory中的各项进行排序
        for key in dataOneDirectory.keys():
            dataOneDirectory[key] = sorted(dataOneDirectory[key], key=(lambda x: [x[0], x[1]]), reverse=False)

        # 重新整理结果
        ret = []
        # ret = [["SampleMass", "SampleIntensity", "Class", "Neutral DBE", "Formula", "Calc m/z", "C", "ion"]]
        for key in dataOneDirectory.keys():
            data = dataOneDirectory[key]
            for item1 in data:
                for item2 in dataDirectory[key][item1[2]]:
                    ret.append(item2)
        return ret


