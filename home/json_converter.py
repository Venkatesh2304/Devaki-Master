import json

def format(normal_row, _format, sum_row=None):
    new = {}
    for key, value in _format.items():
        if type(value) == dict:
            value = format(normal_row, value, sum_row)

        if type(value) == tuple:  # for normal columns
            row = normal_row
        if type(value) == list:  # for sum columnns
            row = sum_row

        if type(value) == tuple or type(value) == list:
            if len(value) == 1:
                # tuple first element is the column of the given key
                new[key] = row[value[0]]
            elif len(value) == 2:
                # tuple second element is the format function of the key applied .
                new[key] = value[1](row[value[0]])
            else:
                try:  # for the default value if the formatter errors like NaN pincode .
                    new[key] = value[1](row[value[0]])
                except:
                    new[key] = value[2](row)
        else:
            new[key] = value
    return new

def rounds(x): return round(float(x), 2)

eway_itm_format = {"productName": ("Product",),
                   "hsnCode": ("HSN", int),
                   "quantity": ("Qty", int),
                   "qtyUnit": "PCS",
                   "taxableAmount": ("Assessable Value", lambda x: round(x, 2)),
                   "sgstRate": ("Tax Rate", lambda x: round(float(x.split("+")[0]), 1)),
                   "cgstRate": ("Tax Rate", lambda x: round(float(x.split("+")[0]), 1))
                   }

eway_bill_format = {"userGstin": ("From_GSTIN", ),
                    "supplyType": "O",
                    "subSupplyType": 1,
                    "subSupplyDesc": "",
                    "docType":  ("To_GSTIN", lambda x: "BIL" if x == "URP" else "INV"),
                    "docNo": ("Doc.No",),
                    "docDate": ("Doc date", lambda x: x.strftime('%d/%m/%Y')),
                    "transType": 1,
                    "fromGstin": ("From_GSTIN", ),
                    "fromPincode": ("From_pin_code", int),
                    "fromStateCode": 33,
                    "actualFromStateCode": 33,
                    "toGstin": ("To_GSTIN", ),
                    "toPincode": ("To_Pin_code", int, lambda row: int(row["From_pin_code"])),
                    "toStateCode": 33,
                    "actualToStateCode": 33,
                    "totalValue": ["Assessable Value", rounds],
                    "cgstValue": ["CGST Amount", rounds],
                    "sgstValue": ["SGST Amount", rounds],
                    "OthValue": ["TCS Amount", rounds],
                    "totInvValue": ("Total Amount", rounds),
                    "transMode": 1,
                    "transDistance": ("Distance level(Km)", int),
                    "transporterName": ("Trans Name",),
                    "transporterId": ("Trans ID",),
                    "transDocNo": ("Trans Docno",),
                    "transDocDate": ("Trans Date", lambda x: x.strftime('%d/%m/%Y')),
                    "vehicleNo": ("Vehicle No",),
                    "vehicleType": "R",
                    "itemList": None
                    }

einv_itm_format = {
    "IsServc": "N",
    "HsnCd": ('HSN Code', lambda x: x.replace('.', '')),
    "Qty": ('Quantity', int),
    "Unit": "PCS",
    "UnitPrice": ('Unit Price', rounds),
    "TotAmt": ('Gross Amount', rounds),
    "Discount": ('Discount', rounds),
    "AssAmt": ('Taxable Value', rounds),
    "GstRt": ('GST Rate (%)', rounds),
    "CgstAmt": ('Cgst Amt (Rs)', rounds),
    "SgstAmt": ('Sgst Amt (Rs)', rounds),
    "TotItemVal": ('Item Total', rounds)
}
einv_bill_format = {
    "Version": "1.1",
    "TranDtls": {
               "TaxSch": "GST",
               "SupTyp": "B2B",
    },
    "DocDtls": {
        "Typ": "INV",
               "No": ('Document Number',),
               "Dt": ('Document Date (DD/MM/YYYY)', lambda x: x.strftime('%d/%m/%Y'))
    },
    "SellerDtls": {
        "Gstin": "33AAPFD1365C1ZR",
        "LglNm": "DEVAKI ENTERPRISES",
        "Addr1": "F/4 , INDUSTRISAL ESTATE , ARIYAMANGALAM",
        "Loc": "TRICHY",
               "Pin": 620010,
               "Stcd": "33"
    },
    "BuyerDtls": {
        "Gstin": ('Buyer GSTIN',),
        "LglNm": ('Buyer Legal Name',),
        "Pos": "33",
               "Addr1": ('Buyer Addr1',),
               "Pin": ('Buyer Pin Code', lambda x:  int(x) if int(x) > 100000 else 620008, 620008),
               "Loc": ('Buyer Location', str),
               "Stcd": "33",
    },
    "ValDtls": {
        "AssVal": ('Total Taxable Value', rounds),
        "CgstVal": ('Cgst Amt', rounds),
        "SgstVal": ('Sgst Amt', rounds),
        "Discount": ('Bill Discount', rounds),
        "RndOffAmt": ('Round Off', rounds),
        "OthChrg": ('TCS Amount', rounds),
        "TotInvVal": ('Total Invoice Value', rounds)
    },
    "ItemList": None}
einv_ewb_format = {
    "TransMode": "1",
    "Distance": ("Distance level(Km)", int),
    "TransDocNo": ("Trans Doc No.",),
    "TransDocDt": ("Trans Doc Date", lambda x: x.strftime('%d/%m/%Y')),
    "VehNo": ("Vehicle No",),
    "VehType": "R",

}


def einvJson(data,isVeh = False):
    data = data.dropna(subset=["Buyer GSTIN"])
    bill_group = data.groupby(by=["Document Number"], as_index=False)
    bills = []
    for idx, bill in bill_group:
        itms = []
        count = 1
        for idx, product in bill.iterrows():
            itm = format(product, einv_itm_format)
            itm["SlNo"] = str(count)
            count += 1
            itms.append(itm)
        _bill = bill 
        bill = format(bill.iloc[0], einv_bill_format, bill.sum())
        bill["ItemList"] = itms
        if isVeh :  #if vehicle details to bea added 
           bill["EwbDtls"] = format(_bill.iloc[0], einv_ewb_format, _bill.sum())

        bills.append(bill)
    json_data = bills
    json_data = json.dumps(json_data).replace('NaN', '""')
    with open("einvoice.json", "w+") as f:
        f.write(json_data)
    return json_data

def ewayJson(data):
    bill_group = data.groupby(by=["Doc.No"], as_index=False)
    bills = []
    for idx, bill in bill_group:
        itms = []
        for idx, product in bill.iterrows():
            itms.append(format(product, eway_itm_format))

        bill = format(bill.iloc[0], eway_bill_format, bill.sum())
        bill["itemList"] = itms
        bills.append(bill)
    json_data = {"version": "1.0.0621", "billLists": bills}
    json_data = json.dumps(json_data).replace('NaN', '""')
    with open("eway.json", "w+") as f:
        f.write(json_data)
    return json_data
