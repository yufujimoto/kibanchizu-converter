import os, sys, codecs, chardet
import xml.etree.ElementTree as et
from lxml import etree
from lxml.etree import XMLParser, parse

# Define the name space.
ns_opg = "{http://fgd.gsi.go.jp/spec/2008/FGD_GMLSchema}"
ns_fgd = "{http://fgd.gsi.go.jp/spec/2008/FGD_GMLSchema}"
ns_gml = "{http://www.opengis.net/gml/3.2}"

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

def convertDem(xmlfile, outdir):
    print("Now Processing: " + xmlfile)
    
    # Define the name space.
    ns_opg = "{http://fgd.gsi.go.jp/spec/2008/FGD_GMLSchema}"
    ns_fgd = "{http://fgd.gsi.go.jp/spec/2008/FGD_GMLSchema}"
    ns_gml = "{http://www.opengis.net/gml/3.2}"
    
    output = os.path.join(outdir, "dem.txt")
    
    # Read the XML file.
    xmlfl = xmlfile
    
    
    # Check the text encoding of the XML file.
    codec = checkEncoding(xmlfl)
    
    # Open the XML file with given encoding.
    data = codecs.open(xmlfl, mode='rt', encoding=codec).read()
    
    # Convert encoding from Shift-JIS to UTF-8 if the encoding is Shift-JIS.
    if codec == "shift_jis":
        data = data.replace('encoding="Shift_JIS"', 'encoding="utf-8"')
    
    data = data.encode('utf-8')
    
    # Parsing the XML string.
    root = et.fromstring(data)
    dems = root.findall(ns_opg + 'DEM')
    
    # Open the output file and Write the first column if required.
    if not os.path.exists(output):
        outfl = open(output, "w")
        outfl.write("Latitude:Longitude:Category:Altitude\n")
    else:
        outfl = open(output, "a")
    
    for dem in dems:
        # Get the metadata information.
        print dem.tag, dem.attrib
        
        fid = dem.find(ns_fgd + "fid").text                                         # Feature ID
        frm = dem.find(ns_fgd + "lfSpanFr").find(ns_gml + "timePosition").text      # Date from
        ddt = dem.find(ns_fgd + "devDate").find(ns_gml + "timePosition").text       # Date of developed
        orgGILvl = dem.find(ns_fgd + "orgGILvl").text                               # GI Level
        orgMDId = dem.find(ns_fgd + "orgMDId").text                                 # MD ID
        meshtype = dem.find(ns_fgd + "type").text                                   # Mesh type
        meshcode = dem.find(ns_fgd + "mesh").text                                   # Mesh code
        
        # Get the coverage information.
        covs = dem.findall(ns_fgd + "coverage")
        
        for cov in covs:
            # Get the basic information about coverage.
            bnd = cov.find(ns_gml + "boundedBy")
            srs = bnd.find(ns_gml + "Envelope").get("srsName")                      # SRS name
            
            # Get the geographic boundary.
            lc = bnd.find(".//" + ns_gml + "lowerCorner").text.strip().split(" ")   # Coodinates of the lower corner
            uc = bnd.find(".//" + ns_gml + "upperCorner").text.strip().split(" ")   # Coodinates of the upper corner
            
            mh = float(uc[0]) - float(lc[0])                                        # Geographic width
            mw = float(uc[1]) - float(lc[1])                                        # Geographic height
            
            
            st_x, st_y = cov.find(".//" + ns_gml + "startPoint").text.strip().split(" ")
            
            # Get the pixcel boundary.
            gdm = cov.find(ns_gml + "gridDomain")
            gl = gdm.find(".//" + ns_gml + "low").text.strip().split(" ")
            gh = gdm.find(".//" + ns_gml + "high").text.strip().split(" ")
            pw = int(gh[0]) - int(gl[0])                                            # Width in pixel
            ph = int(gh[1]) - int(gl[1])                                            # Height in pixel
            
            # Get the pixcel size in geographic space.
            w = mw / pw
            h = mh / ph
            
            # Scale to grid centroid area
            lc[0] = float(lc[0])-(h/2)
            lc[1] = float(lc[1])+(w/2)
            uc[0] = float(uc[0])+(h/2)
            uc[1] = float(uc[1])-(w/2)
            
            mh = float(uc[0]) - float(lc[0])
            mw = float(uc[1]) - float(lc[1]) 
            
            w = mw / pw
            h = mh / ph
            
            # Get the record.
            rst = cov.find(ns_gml + "rangeSet")
            tpl = rst.find(".//" + ns_gml + "tupleList").text.strip().split("\n")
            
            # Get the each entry and write to CSV file.
            cnt = 0
            
            print(len(tpl), int(ph+1)*int(pw))
            
            for i in range(int(ph), -1, -1):
                if i >= st_y:
                    lat = float(lc[0]) + (h * i)
                    for j in range(0, int(pw) + 1):
                        if j >= st_x:
                            lon = float(lc[1]) + (w * j)
                            cat, alt = tpl[cnt].split(",")
                            strln = str(lat) + ":" + str(lon) + ":" + cat + ":" + alt + "\n"
                            strln = strln.encode("utf-8")
                            outfl.write(strln)
                            cnt = cnt + 1
                    
    
    outfl.close()

def convertBase(xmlfile, outdir):
    print("Now Processing: " + xmlfile)
    
    strln_cstline = ""
    strln_admpt = ""
    strln_admarea = ""
    strln_admbdry = ""
    strln_commbdry = ""
    strln_commpt = ""
    strln_wa = ""
    strln_wl = ""
    strln_wstra = ""
    strln_wstrl = ""
    strln_rdedg = ""
    strln_rdcompt = ""
    strln_railcl = ""
    strln_blda = ""
    strln_bldl = ""
    strln_cntr = ""
    strln_elevpt = ""
    strln_gcp = ""
    
    # Read the XML file.
    data = open(xmlfile).read()
    
    # Parsing the XML string.
    root = et.fromstring(data)
    feat_cnt = 0
    
    if root.tag == ns_fgd + "Dataset":
        for feat in root:
            # Coastline.
            if feat.tag == ns_opg + "Cstline":
                # Get the metadata information.
                fid = feat.find(ns_fgd + "fid").text                                         # Feature ID
                frm = feat.find(ns_fgd + "lfSpanFr").find(ns_gml + "timePosition").text      # Date from
                ddt = feat.find(ns_fgd + "devDate").find(ns_gml + "timePosition").text       # Date of developed
                orgGILvl = feat.find(ns_fgd + "orgGILvl").text                               # GI Level
                cate = feat.find(ns_fgd + "type").text
                loc = feat.find(ns_fgd + "loc")
                poly = getGmlPolyline(loc)
                
                # Write to text the file.
                strln = fid + ":" + frm + ":" + ddt + ":" + orgGILvl + ":" + cate + ":" + poly + "\n"
                strln_cstline = strln_cstline + strln.encode("utf-8")
            
            # Administrative Area
            elif feat.tag == ns_opg + 'AdmArea':               
                # Get the metadata information.
                fid = feat.find(ns_fgd + "fid").text                                         # Feature ID
                frm = feat.find(ns_fgd + "lfSpanFr").find(ns_gml + "timePosition").text      # Date from
                ddt = feat.find(ns_fgd + "devDate").find(ns_gml + "timePosition").text       # Date of developed
                orgGILvl = feat.find(ns_fgd + "orgGILvl").text                               # GI Level
                cate = feat.find(ns_fgd + "type").text
                name = feat.find(ns_fgd + "name").text
                code = feat.find(ns_fgd + "admCode").text
                area = feat.find(ns_fgd + "area")
                poly = getGmlPolygon(area)
                
                # Write to text the file.
                strln = fid + ":" + frm + ":" + ddt + ":" + orgGILvl + ":" + code + ":" + name + ":" + cate + ":" + poly + "\n"
                strln_admarea = strln_admarea + strln.encode("utf-8")
                
            # Boundaries of administrative areas.
            elif feat.tag == ns_opg + "AdmBdry":
                # Get the metadata information.
                fid = feat.find(ns_fgd + "fid").text                                         # Feature ID
                frm = feat.find(ns_fgd + "lfSpanFr").find(ns_gml + "timePosition").text      # Date from
                ddt = feat.find(ns_fgd + "devDate").find(ns_gml + "timePosition").text       # Date of developed
                orgGILvl = feat.find(ns_fgd + "orgGILvl").text                               # GI Level
                cate = feat.find(ns_fgd + "type").text
                loc = feat.find(ns_fgd + "loc")
                poly = getGmlPolyline(loc)
                
                # Write to text the file.
                strln = fid + ":" + frm + ":" + ddt + ":" + orgGILvl + ":" + cate + ":" + poly + "\n"
                strln_admbdry = strln_admbdry + strln.encode("utf-8")
                
            # Representative point of the administrative area.
            elif feat.tag == ns_opg + 'AdmPt':
                # Get the metadata information.
                fid = feat.find(ns_fgd + "fid").text                                         # Feature ID
                frm = feat.find(ns_fgd + "lfSpanFr").find(ns_gml + "timePosition").text      # Date from
                ddt = feat.find(ns_fgd + "devDate").find(ns_gml + "timePosition").text       # Date of developed
                orgGILvl = feat.find(ns_fgd + "orgGILvl").text                               # GI Level
                cate = feat.find(ns_fgd + "type").text
                name = feat.find(ns_fgd + "name").text
                code = feat.find(ns_fgd + "admCode").text
                pos = feat.find(ns_fgd + "pos")
                pnt = getGmlPoint(pos)
                
                # Write to text the file.
                strln = fid + ":" + frm + ":" + ddt + ":" + orgGILvl + ":" + code + ":" + name + ":" + cate + ":" + pnt + "\n"
                strln_admpt = strln_admpt + strln.encode("utf-8")
                
            elif feat.tag == ns_opg + "CommBdry":
                # Get the metadata information.
                fid = feat.find(ns_fgd + "fid").text                                         # Feature ID
                frm = feat.find(ns_fgd + "lfSpanFr").find(ns_gml + "timePosition").text      # Date from
                ddt = feat.find(ns_fgd + "devDate").find(ns_gml + "timePosition").text       # Date of developed
                orgGILvl = feat.find(ns_fgd + "orgGILvl").text                               # GI Level
                cate = feat.find(ns_fgd + "type").text
                loc = feat.find(ns_fgd + "loc")
                poly = getGmlPolyline(loc)
                
                # Write to text the file.
                strln = fid + ":" + frm + ":" + ddt + ":" + orgGILvl + ":" + cate + ":" + poly + "\n"
                strln_commbdry = strln_commbdry + strln.encode("utf-8")
                
            # Representative point of the administrative area.
            elif feat.tag == ns_opg + 'CommPt':
                # Get the metadata information.
                fid = feat.find(ns_fgd + "fid").text                                         # Feature ID
                frm = feat.find(ns_fgd + "lfSpanFr").find(ns_gml + "timePosition").text      # Date from
                ddt = feat.find(ns_fgd + "devDate").find(ns_gml + "timePosition").text       # Date of developed
                orgGILvl = feat.find(ns_fgd + "orgGILvl").text                               # GI Level
                cate = feat.find(ns_fgd + "type").text
                name = feat.find(ns_fgd + "name").text
                code = feat.find(ns_fgd + "admCode").text
                pos = feat.find(ns_fgd + "pos")
                pnt = getGmlPoint(pos)
                
                # Write to text the file.
                strln = fid + ":" + frm + ":" + ddt + ":" + orgGILvl + ":" + code + ":" + name + ":" + cate + ":" + pnt + "\n"
                strln_commpt = strln_commpt + strln.encode("utf-8")
            # Water areas
            elif feat.tag == ns_opg + 'WA':
                # Get the metadata information.
                fid = feat.find(ns_fgd + "fid").text                                         # Feature ID
                frm = feat.find(ns_fgd + "lfSpanFr").find(ns_gml + "timePosition").text      # Date from
                ddt = feat.find(ns_fgd + "devDate").find(ns_gml + "timePosition").text       # Date of developed
                orgGILvl = feat.find(ns_fgd + "orgGILvl").text                               # GI Level
                cate = feat.find(ns_fgd + "type").text
                area = feat.find(ns_fgd + "area")
                poly = getGmlPolygon(area)
                
                # Write to text the file.
                strln = fid + ":" + frm + ":" + ddt + ":" + orgGILvl + ":" + cate + ":" + poly + "\n"
                strln_wa = strln_wa + strln.encode("utf-8")
                
            # Boundaries of Water areas.
            elif feat.tag == ns_opg + 'WL':
                # Get the metadata information.
                fid = feat.find(ns_fgd + "fid").text                                         # Feature ID
                frm = feat.find(ns_fgd + "lfSpanFr").find(ns_gml + "timePosition").text      # Date from
                ddt = feat.find(ns_fgd + "devDate").find(ns_gml + "timePosition").text       # Date of developed
                orgGILvl = feat.find(ns_fgd + "orgGILvl").text                               # GI Level
                cate = feat.find(ns_fgd + "type").text
                loc = feat.find(ns_fgd + "loc")
                poly = getGmlPolyline(loc)
                
                # Write to text the file.
                strln = fid + ":" + frm + ":" + ddt + ":" + orgGILvl + ":" + cate + ":" + poly + "\n"
                strln_wl = strln_wl + strln.encode("utf-8")
                
            elif feat.tag == ns_opg + 'WStrA':
                # Get the metadata information.
                fid = feat.find(ns_fgd + "fid").text                                         # Feature ID
                frm = feat.find(ns_fgd + "lfSpanFr").find(ns_gml + "timePosition").text      # Date from
                ddt = feat.find(ns_fgd + "devDate").find(ns_gml + "timePosition").text       # Date of developed
                orgGILvl = feat.find(ns_fgd + "orgGILvl").text                               # GI Level
                cate = feat.find(ns_fgd + "type").text
                area = feat.find(ns_fgd + "area")
                poly = getGmlPolygon(area)
                
                # Write to text the file.
                strln = fid + ":" + frm + ":" + ddt + ":" + orgGILvl + ":" + cate + ":" + poly + "\n"
                strln_wstra = strln_wstra + strln.encode("utf-8")
            
            elif feat.tag == ns_opg + 'WStrL':
                # Get the metadata information.
                fid = feat.find(ns_fgd + "fid").text                                         # Feature ID
                frm = feat.find(ns_fgd + "lfSpanFr").find(ns_gml + "timePosition").text      # Date from
                ddt = feat.find(ns_fgd + "devDate").find(ns_gml + "timePosition").text       # Date of developed
                orgGILvl = feat.find(ns_fgd + "orgGILvl").text                               # GI Level
                cate = feat.find(ns_fgd + "type").text
                loc = feat.find(ns_fgd + "loc")
                poly = getGmlPolyline(loc)
                
                # Write to text the file.
                strln = fid + ":" + frm + ":" + ddt + ":" + orgGILvl + ":" + cate + ":" + poly + "\n"
                strln_wstrl = strln_wstrl + strln.encode("utf-8")
            
            elif feat.tag == ns_opg + "RdEdg":
                # Get the metadata information.
                fid = feat.find(ns_fgd + "fid").text                                         # Feature ID
                frm = feat.find(ns_fgd + "lfSpanFr").find(ns_gml + "timePosition").text      # Date from
                ddt = feat.find(ns_fgd + "devDate").find(ns_gml + "timePosition").text       # Date of developed
                orgGILvl = feat.find(ns_fgd + "orgGILvl").text                               # GI Level
                admOffice = feat.find(ns_fgd + "admOffice").text 
                cate = feat.find(ns_fgd + "type").text
                loc = feat.find(ns_fgd + "loc")
                poly = getGmlPolyline(loc)
                
                # Write to text the file.
                strln = fid + ":" + frm + ":" + ddt + ":" + orgGILvl + ":" + cate + ":" + admOffice + ":" + poly + "\n"
                strln_rdedg = strln_rdedg + strln.encode("utf-8")
                
            elif feat.tag == ns_opg + "RdCompt":
                # Get the metadata information.
                fid = feat.find(ns_fgd + "fid").text                                         # Feature ID
                frm = feat.find(ns_fgd + "lfSpanFr").find(ns_gml + "timePosition").text      # Date from
                ddt = feat.find(ns_fgd + "devDate").find(ns_gml + "timePosition").text       # Date of developed
                orgGILvl = feat.find(ns_fgd + "orgGILvl").text                               # GI Level
                admOffice = feat.find(ns_fgd + "admOffice").text 
                cate = feat.find(ns_fgd + "type").text
                loc = feat.find(ns_fgd + "loc")
                poly = getGmlPolyline(loc)
                
                # Write to text the file.
                strln = fid + ":" + frm + ":" + ddt + ":" + orgGILvl + ":" + cate + ":" + admOffice + ":" + poly + "\n"
                strln_rdcompt = strln_rdedg + strln.encode("utf-8")
                
            elif feat.tag == ns_opg + "RailCL":
                # Get the metadata information.
                fid = feat.find(ns_fgd + "fid").text                                         # Feature ID
                frm = feat.find(ns_fgd + "lfSpanFr").find(ns_gml + "timePosition").text      # Date from
                ddt = feat.find(ns_fgd + "devDate").find(ns_gml + "timePosition").text       # Date of developed
                orgGILvl = feat.find(ns_fgd + "orgGILvl").text                               # GI Level
                cate = feat.find(ns_fgd + "type").text
                loc = feat.find(ns_fgd + "loc")
                poly = getGmlPolyline(loc)
                
                # Write to text the file.
                strln = fid + ":" + frm + ":" + ddt + ":" + orgGILvl + ":" + cate + ":" + poly + "\n"
                strln_railcl = strln_railcl + strln.encode("utf-8")
                
            elif feat.tag == ns_opg + 'BldA':
                # Get the metadata information.
                fid = feat.find(ns_fgd + "fid").text                                         # Feature ID
                frm = feat.find(ns_fgd + "lfSpanFr").find(ns_gml + "timePosition").text      # Date from
                ddt = feat.find(ns_fgd + "devDate").find(ns_gml + "timePosition").text       # Date of developed
                orgGILvl = feat.find(ns_fgd + "orgGILvl").text                               # GI Level
                cate = feat.find(ns_fgd + "type").text
                area = feat.find(ns_fgd + "area")
                poly = getGmlPolygon(area)
                
                # Write to text the file.
                strln = fid + ":" + frm + ":" + ddt + ":" + orgGILvl + ":" + cate + ":" + poly + "\n"
                strln_blda = strln_blda + strln.encode("utf-8")
                
            elif feat.tag == ns_opg + "Cntr":
                # Get the metadata information.
                fid = feat.find(ns_fgd + "fid").text                                         # Feature ID
                frm = feat.find(ns_fgd + "lfSpanFr").find(ns_gml + "timePosition").text      # Date from
                ddt = feat.find(ns_fgd + "devDate").find(ns_gml + "timePosition").text       # Date of developed
                orgGILvl = feat.find(ns_fgd + "orgGILvl").text                               # GI Level
                cate = feat.find(ns_fgd + "type").text
                alti = feat.find(ns_fgd + "alti").text
                loc = feat.find(ns_fgd + "loc")
                poly = getGmlPolyline(loc)
                
                # Write to text the file.
                strln = fid + ":" + frm + ":" + ddt + ":" + orgGILvl + ":" + cate + ":" + alti + ":" + poly + "\n"
                strln_cntr = strln_cntr + strln.encode("utf-8")
                
            elif feat.tag == ns_opg + "BldL":
                # Get the metadata information.
                fid = feat.find(ns_fgd + "fid").text                                         # Feature ID
                frm = feat.find(ns_fgd + "lfSpanFr").find(ns_gml + "timePosition").text      # Date from
                ddt = feat.find(ns_fgd + "devDate").find(ns_gml + "timePosition").text       # Date of developed
                orgGILvl = feat.find(ns_fgd + "orgGILvl").text                               # GI Level
                cate = feat.find(ns_fgd + "type").text
                loc = feat.find(ns_fgd + "loc")
                poly = getGmlPolyline(loc)
                
                # Write to text the file.
                strln = fid + ":" + frm + ":" + ddt + ":" + orgGILvl + ":" + cate + ":" + poly + "\n"
                strln_bldl = strln_bldl + strln.encode("utf-8")
                
            elif feat.tag == ns_opg + "ElevPt":
                # Get the metadata information.
                fid = feat.find(ns_fgd + "fid").text                                         # Feature ID
                frm = feat.find(ns_fgd + "lfSpanFr").find(ns_gml + "timePosition").text      # Date from
                ddt = feat.find(ns_fgd + "devDate").find(ns_gml + "timePosition").text       # Date of developed
                orgGILvl = feat.find(ns_fgd + "orgGILvl").text                               # GI Level
                cate = feat.find(ns_fgd + "type").text
                alti = feat.find(ns_fgd + "alti").text
                pos = feat.find(ns_fgd + "pos")
                pnt = getGmlPoint(pos)
                
                # Write to text the file.
                strln = fid + ":" + frm + ":" + ddt + ":" + orgGILvl + ":" + cate + ":" + str(alti) + ":" + pnt + "\n"
                strln_elevpt = strln_elevpt + strln.encode("utf-8")
                
            elif feat.tag == ns_opg + "GCP":
                # Get the metadata information.
                fid = feat.find(ns_fgd + "fid").text                                         # Feature ID
                frm = feat.find(ns_fgd + "lfSpanFr").find(ns_gml + "timePosition").text      # Date from
                ddt = feat.find(ns_fgd + "devDate").find(ns_gml + "timePosition").text       # Date of developed
                orgGILvl = feat.find(ns_fgd + "orgGILvl").text                               # GI Level
                orgName = feat.find(ns_fgd + "orgName").text 
                cate = feat.find(ns_fgd + "type").text
                alti = feat.find(ns_fgd + "alti").text
                gcpClass = feat.find(ns_fgd + "gcpClass").text
                gcpCode = feat.find(ns_fgd + "gcpCode").text
                B  = feat.find(ns_fgd + "B").text
                L  = feat.find(ns_fgd + "L").text
                altiAcc = feat.find(ns_fgd + "altiAcc").text
                name = feat.find(ns_fgd + "name").text
                
                pos = feat.find(ns_fgd + "pos")
                pnt = getGmlPoint(pos)
                
                # Write to text the file.
                strln = fid + ":" + frm + ":" + ddt + ":" + orgGILvl + ":" + orgName + ":" + cate + ":" + gcpClass + ":" + gcpCode + ":" + name + ":" + B + ":" + L + ":" + altiAcc + ":" + alti + ":" + pnt + "\n"
                strln_gcp = strln_gcp + strln.encode("utf-8")
                
    if strln_cstline != "":
        outfile = os.path.join(outdir, 'Cstline.txt')
        header = "fid:lfSpanFr:devDate:orgGILvl:type:wkt\n"
        
        openAndWriteDoc(outfile, header, strln_cstline)
        
    if strln_admarea != "":
        outfile = os.path.join(outdir, 'AdmArea.txt')
        header = "fid:lfSpanFr:devDate:orgGILvl:admCode:name:type:wkt\n"
        
        openAndWriteDoc(outfile, header, strln_admarea)
        
    if strln_admbdry != "":
        outfile = os.path.join(outdir, 'AdmBdry.txt')
        header = "fid:lfSpanFr:devDate:orgGILvl:type:wkt\n"
        
        openAndWriteDoc(outfile, header, strln_admbdry)
        
    if strln_admpt != "":
        outfile = os.path.join(outdir, 'AdmPt.txt')
        header = "fid:lfSpanFr:devDate:orgGILvl:admCode:name:type:wkt\n"
        
        openAndWriteDoc(outfile, header, strln_admpt)
        
    if strln_commbdry != "":
        outfile = os.path.join(outdir, 'CommBdry.txt')
        header = "fid:lfSpanFr:devDate:orgGILvl:type:wkt\n"
        
        openAndWriteDoc(outfile, header, strln_commpt)
        
    if strln_commpt != "":
        outfile = os.path.join(outdir, 'CommPt.txt')
        header = "fid:lfSpanFr:devDate:orgGILvl:admCode:name:type:wkt\n"
        
        openAndWriteDoc(outfile, header, strln_commpt)
        
    if strln_wa != "":
        outfile = os.path.join(outdir, 'WA.txt')
        header = "fid:lfSpanFr:devDate:orgGILvl:type:wkt\n"
        
        openAndWriteDoc(outfile, header, strln_wl)
        
    if strln_wl != "":
        outfile = os.path.join(outdir, 'WL.txt')
        header = "fid:lfSpanFr:devDate:orgGILvl:type:wkt\n"
        
        openAndWriteDoc(outfile, header, strln_wl)
        
    if strln_wstra != "":
        outfile = os.path.join(outdir, 'WStrA.txt')
        header = "fid:lfSpanFr:devDate:orgGILvl:type:wkt\n"
        
        openAndWriteDoc(outfile, header, strln_wstra)
        
    if strln_wstrl != "":
        outfile = os.path.join(outdir, 'WStrL.txt')
        header = "fid:lfSpanFr:devDate:orgGILvl:type:wkt\n"
        
        openAndWriteDoc(outfile, header, strln_wstrl)
        
    if strln_rdedg != "":
        outfile = os.path.join(outdir, 'RdEdg.txt')
        header = "fid:lfSpanFr:devDate:orgGILvl:type:admOffice:wkt\n"
        
        openAndWriteDoc(outfile, header, strln_rdedg)
        
    if strln_rdcompt != "":
        outfile = os.path.join(outdir, 'BldA.txt')
        header = "fid:lfSpanFr:devDate:orgGILvl:type:admOffice:wkt\n"
        
        openAndWriteDoc(outfile, header, strln_rdcompt)
        
    if strln_railcl != "":
        outfile = os.path.join(outdir, 'RailCL.txt')
        header = "fid:lfSpanFr:devDate:orgGILvl:type:wkt\n"
        
        openAndWriteDoc(outfile, header, strln_railcl)
        
    if strln_blda != "":
        outfile = os.path.join(outdir, 'BldA.txt')
        header = "fid:lfSpanFr:devDate:orgGILvl:type:wkt\n"
        
        openAndWriteDoc(outfile, header, strln_blda)
        
    if strln_bldl != "":
        outfile = os.path.join(outdir, 'BldL.txt')
        header = "fid:lfSpanFr:devDate:orgGILvl:type:wkt\n"
        
        openAndWriteDoc(outfile, header, strln_bldl)
        
    if strln_cntr != "":
        outfile = os.path.join(outdir, 'Cntr.txt')
        header = "fid:lfSpanFr:devDate:orgGILvl:type:altitude:wkt\n"
        
        openAndWriteDoc(outfile, header, strln_cntr)
        
    if strln_elevpt != "":
        outfile = os.path.join(outdir, 'ElevPt.txt')
        header = "fid:lfSpanFr:devDate:orgGILvl:type:altitude:wkt\n"
        
        openAndWriteDoc(outfile, header, strln_elevpt)
    
    if strln_gcp != "":
        outfile = os.path.join(outdir, 'GCP.txt')
        header = "fid:lfSpanFr:devDate:orgGILvl:type:altitude:wkt\n"
        
        openAndWriteDoc(outfile, header, strln_gcp)
        






