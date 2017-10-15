#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, codecs, chardet
import xml.etree.ElementTree as et
from lxml import etree
from lxml.etree import XMLParser, parse

# Define the name space.
ns_opg = "{http://fgd.gsi.go.jp/spec/2008/FGD_GMLSchema}"
ns_fgd = "{http://fgd.gsi.go.jp/spec/2008/FGD_GMLSchema}"
ns_gml = "{http://www.opengis.net/gml/3.2}"
ns_jmp = "{http://zgate.gsi.go.jp/ch/jmp}"
ns_ksj = "{http://nlftp.mlit.go.jp/ksj/schemas/ksj-app}"
ns_xln = "{http://www.w3.org/1999/xlink}"
ns_xsi = "{http://www.w3.org/2001/XMLSchema-instance}"

def checkEncoding(filename):
    p = XMLParser(huge_tree=True)
    
    with open(filename, 'r') as xmlfile:
        tree = etree.parse(xmlfile,parser=p)
        return(tree.docinfo.encoding.lower())

def openAndWriteDoc(filename, header, data):
    if os.path.exists(filename) != True:
        output = open(filename, "w")
        output.write(header)
    else:
        output = open(filename, "a")
    output.write(data)
    output.close()

def getGmlPoint(geom):
    point = geom.find(".//" + ns_gml + "pos").text.split(" ")
    return "POINT(" + point[1] + " " + point[0] + ")"

def getGmlPolyline(geom):
    parts = ""
    part = ""
    
    for seg in geom:
        posl = seg.find(".//" + ns_gml + "posList").text.strip().split("\n")
    ctrl = ""
    for item in posl:
        entry = item.split(" ")
        ctrl = ctrl + entry[1] + " " + entry[0] + ","
    return "LINESTRING(" + ctrl.strip(",") + ")"

def getGmlPolygon(geom):
    parts = ""
    inte = ""
    exte = ""
    
    pchs = geom.find(".//" + ns_gml + "PolygonPatch")
    
    for rngs in pchs:
        ctrl = ""
        if rngs.tag == ns_gml + "exterior":
            segs = rngs.find(".//" + ns_gml + "segments")
            for seg in segs:
                posl = seg.find(".//" + ns_gml + "posList").text.strip().split("\n")
            for item in posl:
                entry = item.split(" ")
                ctrl = ctrl + entry[1] + " " + entry[0] + ","
            exte = "(" + ctrl.strip(",") + ")"
        if rngs.tag == ns_gml + "interior":
            segs = rngs.find(".//" + ns_gml + "segments")
            for seg in segs:
                posl = seg.find(".//" + ns_gml + "posList").text.strip().split("\n")
            for item in posl:
                entry = item.split(" ")
                ctrl = ctrl + entry[1] + " " + entry[0] + ","
            inte = "(" + ctrl.strip(",") + ")"
        parts = exte + "," + inte
    return "POLYGON(" + parts.strip(",") + ")"

def convertJmp(xmlfile, outdir):
    print("Now Processing: " + xmlfile)
    
    # Read the XML file.
    data = open(xmlfile).read()
    
    # Parsing the XML string.
    root = et.fromstring(data)
    feat_cnt = 0
    
    if root.tag == ns_ksj + "Dataset":
        if root.attrib[ns_gml+"id"] == "N07Dataset":
            parseBusRoute(root, outdir)
        elif root.attrib[ns_gml+"id"] == "P11Dataset":
            parseBusStop(root, outdir)
        elif root.attrib[ns_gml+"id"] == "C23Dataset":
            parseCoastLine(root, outdir)
        elif root.attrib[ns_gml+"id"] == "P23Dataset":
            parseCoastFacilities(root, outdir)

def parseBusStop(root, outdir):
    strln_busStop = ""
    strln_routeInfo = ""
    description = root.find(".//" + ns_gml + "description").text
    busStops = root.findall(".//" + ns_ksj + "BusStop")
    
    for busStop in busStops:
        uuid = str(busStop.attrib[ns_gml + "id"].encode("utf-8"))
        refid = busStop.find(ns_ksj + "position").attrib[ns_xln + "href"].replace("#","")
            
        busStopName = str(busStop.find(ns_ksj + "busStopName").text.encode("utf-8"))
        
        point = root.find(".//" + ns_gml + "Point[@" + ns_gml + "id='" + refid + "']")
        wkt_geom = getGmlPoint(point)
        
        strln_busStop = strln_busStop + uuid + ":" + busStopName + ":" + wkt_geom + "\n"
        
        routeInfo = busStop.findall(ns_ksj + "busRouteInformation")
        for route in routeInfo:
            busType = ""
            busTypeCode = route.find(".//" + ns_ksj + "busType").text
            if busTypeCode == "1":
                busType = "民間バス"
            elif busTypeCode == "2":
                busType = "公営バス"
            elif busTypeCode == "3":
                busType = "コミュニティバス"
            elif busTypeCode == "4":
                busType = "デマンドバス"
            elif busTypeCode == "5":
                busType = "その他"
            else:
                busType == "不明"
            
            busOperationCompany = str(route.find(".//" + ns_ksj + "busOperationCompany").text.encode("utf-8"))
            busLineName = str(route.find(".//" + ns_ksj + "busLineName").text.encode("utf-8"))
            
            strln_routeInfo = strln_routeInfo + uuid + ":" + busType + ":" + busOperationCompany + ":" + busLineName + "\n"
    
    outfile_stop = os.path.join(outdir, 'busStop.txt')
    header_stop = "id:busStopName:node\n"
    openAndWriteDoc(outfile_stop, header_stop, strln_busStop)
    
    outfile_route = os.path.join(outdir, 'busStopRouteInfo.txt')
    header_route = "id:busType:busOperationCompany:busLineName\n"
    openAndWriteDoc(outfile_route, header_route, strln_routeInfo)
        
def parseBusRoute(root, outdir):
    strln_busRoute = ""
    description = root.find(".//" + ns_gml + "description").text
    busRoutes = root.findall(".//" + ns_ksj + "BusRoute")
    
    for busRoute in busRoutes:
        uuid = busRoute.attrib[ns_gml + "id"]
        refid = busRoute.find(ns_ksj + "brt").attrib[ns_xln + "href"].replace("#","")
        
        busType = None
        busTypeCode = busRoute.find(ns_ksj + "bsc").text
        if busTypeCode == "1":
            busType = "民間バス"
        elif busTypeCode == "2":
            busType = "公営バス"
        elif busTypeCode == "3":
            busType = "コミュニティバス"
        elif busTypeCode == "4":
            busType = "デマンドバス"
        elif busTypeCode == "5":
            busType = "その他"
        else:
            busType == "不明"
        
        company = str(busRoute.find(ns_ksj + "boc").text.encode("utf-8"))
        lineName = str(busRoute.find(ns_ksj + "bln").text.encode("utf-8"))
        linesPerDay = str(busRoute.find(ns_ksj + "rpd").text.encode("utf-8"))
        linesPerSat = str(busRoute.find(ns_ksj + "rps").text.encode("utf-8"))
        linesPerSun = str(busRoute.find(ns_ksj + "rph").text.encode("utf-8"))
        
        edge = root.find(".//" + ns_gml + "Curve[@" + ns_gml + "id='" + refid + "']")
        wkt_geom = getGmlPolyline(edge)
        
        strln_busRoute = strln_busRoute + uuid + ":" + busType + ":" + company + ":" + lineName + ":" + linesPerDay + ":" + linesPerSat + ":" + linesPerSun + ":" + wkt_geom + "\n"
        
    outfile = os.path.join(outdir, 'busRoute.txt')
    header = "id:busType:busOperationCompany:busLineName:linesPerWorkday:linesPerSat:linesPerSun:edge\n"
    openAndWriteDoc(outfile, header, strln_busRoute)

def parseCoastLine(root, outdir):
    strln_coastLine = ""
    description = root.find(".//" + ns_gml + "description").text
    coastLines = root.findall(".//" + ns_ksj + "Coastline")
    
    for coastLine in coastLines:
        uuid = coastLine.attrib[ns_gml + "id"]
        refid = coastLine.find(ns_ksj + "location").attrib[ns_xln + "href"].replace("#","")
        
        adminCode = ""
        compAuthCode = ""
        compAuth = ""
        areaNumber = ""
        areaName = ""
        coastAdminCode = ""
        coastAdmin = ""
        coastAdminName = ""
        branchingBay = ""
        
        if not coastLine.find(ns_ksj + "administrativeAreaCode") == None:
            adminCode = str(coastLine.find(ns_ksj + "administrativeAreaCode").text.encode("utf-8"))     # 行政区域コード
            
        if not coastLine.find(ns_ksj + "competentAuthorities") == None:
            compAuthCode = str(coastLine.find(ns_ksj + "competentAuthorities").text.encode("utf-8"))    # 所管官庁コード
            
            # Decode the competent authorities code.
            if compAuthCode == "1":
                compAuth = "国土交通省河川局"
            elif compAuthCode == "2":
                compAuth = "国土交通省港湾局"
            elif compAuthCode == "3":
                compAuth = "農林水産省農村振興局"
            elif compAuthCode == "4":
                compAuth = "農林水産省水産庁"
            elif compAuthCode == "5":
                compAuth = "農振河川共管"
            elif compAuthCode == "6":
                compAuth = "不明(原典資料を入手できなかった場合)"
            elif compAuthCode == "7":
                compAuth = "不明(原典資料をデータ化できなかった場合)"
            elif compAuthCode == "0":
                compAuth = "その他"
            else:
                compAuth = "unknown"
        
        if not coastLine.find(ns_ksj + "areaNumber") == None:
            areaNumber = str(coastLine.find(ns_ksj + "areaNumber").text.encode("utf-8"))                # 海岸保全区域番号
        if not coastLine.find(ns_ksj + "areaName") == None:
            areaName = str(coastLine.find(ns_ksj + "areaName").text.encode("utf-8"))                    # 海岸保全区域・海岸名
        if not coastLine.find(ns_ksj + "administrator") == None:
            coastAdminCode = str(coastLine.find(ns_ksj + "administrator").text.encode("utf-8"))         # 海岸保全区域・海岸管理者
            
            # Decode the coast line administrator code.
            if coastAdminCode == "1":
                coastAdmin = "都道府県知事"
            elif coastAdminCode == "2":
                coastAdmin = "市町村長"
            elif coastAdminCode == "3":
                coastAdmin = "一般事務組合"
            elif coastAdminCode == "4":
                coastAdmin = "港務局"
            elif coastAdminCode == "9":
                coastAdmin = "不明"
            elif coastAdminCode == "0":
                coastAdmin = "その他"
            else:
                compAuth = "unknown"
        if not coastLine.find(ns_ksj + "administratorname") == None:
            coastAdminName = str(coastLine.find(ns_ksj + "administratorname").text.encode("utf-8"))     # 海岸保全区域・海岸管理者名
        if not coastLine.find(ns_ksj + "branchingBay") == None:
            branchingBay = str(coastLine.find(ns_ksj + "branchingBay").text.encode("utf-8"))            # 河口
        
        edge = root.find(".//" + ns_gml + "Curve[@" + ns_gml + "id='" + refid + "']")                   # 場所
        wkt_geom = getGmlPolyline(edge)
        
        strln_coastLine = strln_coastLine + uuid + ":" + adminCode + ":" + compAuth + ":" + areaNumber + ":" + areaName + ":" + coastAdmin + ":" + coastAdminName + ":" + branchingBay + ":" + wkt_geom + "\n"
        
    outfile = os.path.join(outdir, 'coastLine.txt')
    header = "id:administrativeAreaCode:competentAuthorities:areaNumber:areaName:administrator:administratorname:branchingBay:edge\n"
    openAndWriteDoc(outfile, header, strln_coastLine)

def parseCoastFacilities(root, outdir):
    strln_Facilities = ""
    strln_Facilities_pt = ""
    strln_Facilities_cv = ""
    
    description = root.find(".//" + ns_gml + "description").text
    facilities_pts = root.findall(".//" + ns_ksj + "CoastalFacilities_Point")
    facilities_lns = root.findall(".//" + ns_ksj + "CoastalFacilities_Line")
    
    for facilities_pt in facilities_pts:
        uuid = facilities_pt.attrib[ns_gml + "id"]
        uuid2 = uuid.replace("_P_","_")
        refid = facilities_pt.find(ns_ksj + "position").attrib[ns_xln + "href"].replace("#","")
        
        adminCode = ""      # 行政コード
        compAuth = ""       # 所管省庁
        facilAdmin = ""     # 管理者
        baseLevel = ""      # 基準面
        MaxPresent = ""     # 天端高最大(現況)
        MinPresent = ""     # 天端高最小(現況)
        MaxPlan = ""        # 天端高最大(計画)
        MinPlan = ""        # 天端高最小(計画)
        
        elem_adminCode = facilities_pt.find(ns_ksj + "administrativeAreaCode")
        elem_compAuth = facilities_pt.find(ns_ksj + "competentAuthority")
        elem_facilAdmin = facilities_pt.find(ns_ksj + "administrator")
        elem_baseLevel = facilities_pt.find(ns_ksj + "baseLevel")
        elem_MaxPresent = facilities_pt.find(ns_ksj + "copeLevelMaxPresent")
        elem_MinPresent = facilities_pt.find(ns_ksj + "copeLevelMinPresent")
        elem_MaxPlan = facilities_pt.find(ns_ksj + "copeLevelMaxPlan")
        elem_MinPlan = facilities_pt.find(ns_ksj + "copeLevelMinPlan")
        
        if not elem_adminCode == None:
            if not elem_adminCode.text == None:
                adminCode = elem_adminCode.text.encode("utf-8")      # 行政区域コード
        if not elem_compAuth == None:
            if not elem_compAuth.text == None:
                compAuth = elem_compAuth.text.encode("utf-8")        # 所管官庁
        if not elem_facilAdmin == None:
            if not elem_facilAdmin.text == None:
                facilAdmin = elem_facilAdmin.text.encode("utf-8")    # 管理者
        if not elem_baseLevel == None:
            if not elem_baseLevel.text == None:
                baseLevel = elem_baseLevel.text.encode("utf-8")      # 基準面
        if not elem_MaxPresent == None:
            if not elem_MaxPresent.text == None:
                MaxPresent = elem_MaxPresent.text.encode("utf-8")    # 天端高最大(現況)
        if not elem_MinPresent == None:
            if not elem_MinPresent.text == None:
                MinPresent = elem_MinPresent.text.encode("utf-8")    # 天端高最小(現況)
        if not elem_MaxPlan == None:
            if not elem_MaxPlan.text == None:
                MaxPlan = elem_MaxPlan.text.encode("utf-8")          # 天端高最大(計画)
        if not elem_MinPlan == None:
            if not elem_MinPlan.text == None:
                MinPlan = elem_MinPlan.text.encode("utf-8")          # 天端高最小(計画)
        
        facilityType_bank = ""
        facilityType_groin = ""
        facilityType_bankProtection = ""
        facilityType_breastWall = ""
        facilityType_offshoreBreakwater = ""
        facilityType_sandyBeach = ""
        facilityType_otherFacilities = ""
        
        facilityTypes = facilities_pt.find(ns_ksj + "facilityType")
        
        for facilityType in facilityTypes:
            elem_facilityType_bank = facilityType.find(".//" + ns_ksj + "bank")
            elem_facilityType_groin = facilityType.find(".//" + ns_ksj + "groin")
            elem_facilityType_bankProtection = facilityType.find(".//" + ns_ksj + "bankProtection")
            elem_facilityType_breastWall = facilityType.find(".//" + ns_ksj + "breastWall")
            elem_facilityType_offshoreBreakwater = facilityType.find(".//" + ns_ksj + "offshoreBreakwater")
            elem_facilityType_sandyBeach = facilityType.find(".//" + ns_ksj + "sandyBeach")
            elem_facilityType_otherFacilities = facilityType.find(".//" + ns_ksj + "otherFacilities")
            
            if not elem_facilityType_bank.text == None:
                facilityType_bank = elem_facilityType_bank.text.encode("utf-8")                            # 堤防
            if not elem_facilityType_groin.text == None:
                facilityType_groin = elem_facilityType_groin.text.encode("utf-8")                          # 突堤
            if not elem_facilityType_bankProtection.text == None:
                facilityType_bankProtection = elem_facilityType_bankProtection.text.encode("utf-8")        # 護岸
            if not elem_facilityType_breastWall.text == None:
                facilityType_breastWall = elem_facilityType_breastWall.text.encode("utf-8")                # 胸壁
            if not elem_facilityType_offshoreBreakwater.text == None:
                facilityType_offshoreBreakwater = elem_facilityType_offshoreBreakwater.text.encode("utf-8")# 離岸堤
            if not elem_facilityType_sandyBeach.text == None:
                facilityType_sandyBeach = elem_facilityType_sandyBeach.text.encode("utf-8")                # 砂浜
            if not elem_facilityType_otherFacilities.text == None:
                facilityType_otherFacilities = elem_facilityType_otherFacilities.text.encode("utf-8")      # その他の施設 
        
        strln_Facilities = strln_Facilities + uuid2 + ":" + adminCode + ":" + compAuth + ":" +  facilAdmin + ":" + \
                           baseLevel + ":" + MaxPresent + ":" + MaxPlan + ":" + MinPlan + ":" + \
                           facilityType_bank + ":" + facilityType_groin + ":" + facilityType_bankProtection + ":" + \
                           facilityType_breastWall + ":" + facilityType_offshoreBreakwater + ":" + facilityType_sandyBeach + ":" + \
                           facilityType_otherFacilities + "\n"
        
        point = root.find(".//" + ns_gml + "Point[@" + ns_gml + "id='" + refid + "']")
        wkt_geom = getGmlPoint(point)
        
        strln_Facilities_pt = strln_Facilities_pt + uuid + ":" + uuid2 + ":" + wkt_geom + "\n"
    
    outfile_attrib = os.path.join(outdir, 'coastFacilities.txt')
    header_attrib = "id:AdministratorCode:competentAuthority:Administrator:baseLevel:copeLevelMaxPresent:copeLevelMinPresent:copeLevelMaxPlan:copeLevelMinPlan\n"
    openAndWriteDoc(outfile_attrib, header_attrib, strln_Facilities)
    
    outfile_point = os.path.join(outdir, 'coastFacilities_point.txt')
    header_point = "id:id2:point\n"
    openAndWriteDoc(outfile_point, header_point, strln_Facilities_pt)
    
    for facilities_ln in facilities_lns:
        uuid = facilities_ln.attrib[ns_gml + "id"]
        uuid2 = uuid.replace("_P_","_")
        refid = facilities_ln.find(ns_ksj + "location").attrib[ns_xln + "href"].replace("#","")
        
        adminCode = ""      # 行政コード
        compAuth = ""       # 所管省庁
        facilAdmin = ""     # 管理者
        baseLevel = ""      # 基準面
        MaxPresent = ""     # 天端高最大(現況)
        MinPresent = ""     # 天端高最小(現況)
        MaxPlan = ""        # 天端高最大(計画)
        MinPlan = ""        # 天端高最小(計画)
        
        elem_adminCode = facilities_ln.find(ns_ksj + "administrativeAreaCode")
        elem_compAuth = facilities_ln.find(ns_ksj + "competentAuthority")
        elem_facilAdmin = facilities_ln.find(ns_ksj + "administrator")
        elem_baseLevel = facilities_ln.find(ns_ksj + "baseLevel")
        elem_MaxPresent = facilities_ln.find(ns_ksj + "copeLevelMaxPresent")
        elem_MinPresent = facilities_ln.find(ns_ksj + "copeLevelMinPresent")
        elem_MaxPlan = facilities_ln.find(ns_ksj + "copeLevelMaxPlan")
        elem_MinPlan = facilities_ln.find(ns_ksj + "copeLevelMinPlan")
        
        if not elem_adminCode == None:
            if not elem_adminCode.text == None:
                adminCode = elem_adminCode.text.encode("utf-8")      # 行政区域コード
        if not elem_compAuth == None:
            if not elem_compAuth.text == None:
                compAuth = elem_compAuth.text.encode("utf-8")        # 所管官庁
        if not elem_facilAdmin == None:
            if not elem_facilAdmin.text == None:
                facilAdmin = elem_facilAdmin.text.encode("utf-8")    # 管理者
        if not elem_baseLevel == None:
            if not elem_baseLevel.text == None:
                baseLevel = elem_baseLevel.text.encode("utf-8")      # 基準面
        if not elem_MaxPresent == None:
            if not elem_MaxPresent.text == None:
                MaxPresent = elem_MaxPresent.text.encode("utf-8")    # 天端高最大(現況)
        if not elem_MinPresent == None:
            if not elem_MinPresent.text == None:
                MinPresent = elem_MinPresent.text.encode("utf-8")    # 天端高最小(現況)
        if not elem_MaxPlan == None:
            if not elem_MaxPlan.text == None:
                MaxPlan = elem_MaxPlan.text.encode("utf-8")          # 天端高最大(計画)
        if not elem_MinPlan == None:
            if not elem_MinPlan.text == None:
                MinPlan = elem_MinPlan.text.encode("utf-8")          # 天端高最小(計画)
        
        facilityType_bank = ""
        facilityType_groin = ""
        facilityType_bankProtection = ""
        facilityType_breastWall = ""
        facilityType_offshoreBreakwater = ""
        facilityType_sandyBeach = ""
        facilityType_otherFacilities = ""
        
        facilityTypes = facilities_ln.find(ns_ksj + "facilityType")
        
        for facilityType in facilityTypes:
            elem_facilityType_bank = facilityType.find(".//" + ns_ksj + "bank")
            elem_facilityType_groin = facilityType.find(".//" + ns_ksj + "groin")
            elem_facilityType_bankProtection = facilityType.find(".//" + ns_ksj + "bankProtection")
            elem_facilityType_breastWall = facilityType.find(".//" + ns_ksj + "breastWall")
            elem_facilityType_offshoreBreakwater = facilityType.find(".//" + ns_ksj + "offshoreBreakwater")
            elem_facilityType_sandyBeach = facilityType.find(".//" + ns_ksj + "sandyBeach")
            elem_facilityType_otherFacilities = facilityType.find(".//" + ns_ksj + "otherFacilities")
            
            if not elem_facilityType_bank.text == None:
                facilityType_bank = elem_facilityType_bank.text.encode("utf-8")                            # 堤防
            if not elem_facilityType_groin.text == None:
                facilityType_groin = elem_facilityType_groin.text.encode("utf-8")                          # 突堤
            if not elem_facilityType_bankProtection.text == None:
                facilityType_bankProtection = elem_facilityType_bankProtection.text.encode("utf-8")        # 護岸
            if not elem_facilityType_breastWall.text == None:
                facilityType_breastWall = elem_facilityType_breastWall.text.encode("utf-8")                # 胸壁
            if not elem_facilityType_offshoreBreakwater.text == None:
                facilityType_offshoreBreakwater = elem_facilityType_offshoreBreakwater.text.encode("utf-8")# 離岸堤
            if not elem_facilityType_sandyBeach.text == None:
                facilityType_sandyBeach = elem_facilityType_sandyBeach.text.encode("utf-8")                # 砂浜
            if not elem_facilityType_otherFacilities.text == None:
                facilityType_otherFacilities = elem_facilityType_otherFacilities.text.encode("utf-8")      # その他の施設
        
        strln_Facilities = strln_Facilities + uuid + ":" + uuid2 + ":" + adminCode + ":" + compAuth  + ":" +  facilAdmin + ":" + \
                           baseLevel + ":" + MaxPresent + ":" + MaxPlan + ":" + MinPlan + ":" + \
                           facilityType_bank + ":" + facilityType_groin + ":" + facilityType_bankProtection + ":" + \
                           facilityType_breastWall + ":" + facilityType_offshoreBreakwater + ":" + facilityType_sandyBeach + ":" + \
                           facilityType_otherFacilities + "\n"
        
        edge = root.find(".//" + ns_gml + "Curve[@" + ns_gml + "id='" + refid + "']")                       # 場所
        wkt_geom = getGmlPolyline(edge)
        
        strln_Facilities_cv = strln_Facilities_cv + uuid + ":" + uuid2 + ":" + wkt_geom + "\n"
    
    openAndWriteDoc(outfile_attrib, header_attrib, strln_Facilities)
    uniqlines = set(open(outfile_attrib).readlines())
    new_outfile_attrib = open(outfile_attrib, 'w').writelines(set(uniqlines))
    new_outfile_attrib.close()
    
    outfile_line = os.path.join(outdir, 'coastFacilities_line.txt')
    header_line = "id:id2:point\n"
    openAndWriteDoc(outfile_line, header_line, strln_Facilities_cv)
    
#convertJmp('/home/yufujimoto/Desktop/N07-11_29_GML/N07-11_29.xml','/home/yufujimoto/Desktop' )
#convertJmp('/home/yufujimoto/Desktop/P11-10_29_GML/P11-10_29-jgd-g.xml','/home/yufujimoto/Desktop' )
#convertJmp('/home/yufujimoto/Desktop/C23-06_47_GML/C23-06_47-g.xml','/home/yufujimoto/Desktop' )
convertJmp('/home/yufujimoto/Desktop/P23-12_01_GML/P23-12_01.xml','/home/yufujimoto/Desktop')