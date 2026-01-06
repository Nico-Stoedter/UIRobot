def interpret_data(header, message_id, data_bytes):
    # Interpretiere basierend auf dem Feedback-Header und der Nachrichts-ID
    results={} #return dictionary
    if header == "AA":  # Feedback-Header "AA"
        if message_id == "DD":  # SETADR=X; don't implement
            pass
        elif message_id == "D0": # ADR=5; don't implement
            pass
        elif message_id == "AD":  # "g***;" group settings - don't implement
            pass
        elif message_id == "A0":  # ENAη; ENAxFFFF; set enable time, boot time after η ms enable - don't implement
            pass
        elif message_id == "B0":  # MCFη; MCF; master configuration register
            if len(data_bytes)==3: #all messages should return 3 data bytes
                mcf = get_16bit(data_bytes) #master config register
                if mcf < 0:
                    mcf = (1 << 16) + mcf
                dmcf = analyze_MCFG(mcf)
                results.update(dmcf)
        elif message_id == "B1":  # MACη; MAC; set acceleration rate η
            if len(data_bytes)==6:
                AM=data_bytes[0]
                accRate = get_32bit(data_bytes[1:])
                results.update({"AM": AM, "accRate": accRate}) 
        elif message_id == "B2":  # MDEη; MDE; set deceleration rate η
            if len(data_bytes) == 6:
                DM=data_bytes[0]
                decRate = get_32bit(data_bytes[1:])
                results.update({"DM": DM, "decRate": decRate})
        elif message_id == "B3":  # MMSη; MMS; Set maximum starting speed η
            if len(data_bytes)==3: #all messages should return 3 data bytes
                mms = get_16bit(data_bytes) #maximum starting speed
                if mms < 0:
                    mms = (1 << 16) + mms
                results.update({"maxStartSpeed": mms})
        elif message_id == "B4":  # MMDη; MMD; Set maximum cessation speed η
            if len(data_bytes)==3: #all messages should return 3 data bytes
                mmd = get_16bit(data_bytes) #maximum cessation speed
                if mmd < 0:
                    mmd = (1 << 16) + mmd
                results.update({"maxStopSpeed": mmd})
        elif message_id == "B5":  # SPDη; set desired speed η
            if len(data_bytes)==3:
                sSpd = get_16bit(data_bytes)
                results.update({"sSpd": sSpd})
        elif message_id == "B6":  # STPη; Set desired incremental displacement η STP0 switches from position tracking to velocity tracking
            if len(data_bytes) == 5: #all messages should return 5 data bytes
                sDisplacement = get_32bit(data_bytes) #set incremental displacement
                results.update({"sDisplacement": sDisplacement})
        elif message_id == "B7":  # ORGη; ORG; Reset the position to a given value η, Set zero/origin position
            pass # ORG; does not return B7 message!!!  -> ORG; CC//B1
        elif message_id == "B8":  # QECη; Set desired quadrature encoder’s position η
            if len(data_bytes)==5: #all messages should return 5 data bytes
                sEncoder = get_32bit(data_bytes) #set encoder position
                results.update({"sEncoder": sEncoder})
        elif message_id == "BA":  # ACR; ACRη; Check auto-current reduction ratio
            if len(data_bytes) == 1: #all messages should return 1 data bytes
                ACR=data_bytes[0]
                results.update({"holdingCurrent": ACR})
        elif message_id == "BC":  # BTRη; BTR; Set CAN network communication bit rate index
            pass #no response
        elif message_id == "C0":  # SCFη; SCF; Set sensor control configuration register η
            if len(data_bytes) == 9:
                s3412conf = get_32bit(data_bytes[0:5])
                S34CON = s3412conf>>16
                S12CON = 0x0000FFFF&s3412conf
                ATCONL = get_16bit(data_bytes[5:7])
                ATCONH = get_16bit(data_bytes[7:])
                results.update({"S34CON": S34CON, "S12CON": S12CON, "ATCONH": ATCONH, "ATCONL": ATCONL})
        elif message_id == "C1":  # DOUη; DOU; Set output TTL level η
            pass #not implemented
        elif message_id == "C2":  # QERη; QER; Set desired quadrature encoder’s position η
            if len(data_bytes) == 3:
                encoderRes = get_16bit(data_bytes)
                results.update({"encoderRes": encoderRes})
        elif message_id == "C9":  # STGη; STG; Set digital input sampling mode
            if len(data_bytes) == 9: #watch out for 1st bit
                sampleTimeS1 = get_16bit(data_bytes[0:3]) #sample time for sensor 1
                sampleTimeS2 = get_16bit(data_bytes[3:6])
                sampleTimeS3 = get_16bit(data_bytes[6:])
                results.update({"sTimeS1": sampleTimeS1,"sTimeS2": sampleTimeS2,"sTimeS3": sampleTimeS3})
        elif message_id == "D1":  # STO; STO; Store motion control parameters
            pass #do not implement, configure in STEPEVA
            #important for limit switch configuration
            #no motion triggered without STO1;STO2;STO3;STO4;STO5;...
        elif message_id == "DA":  # ICFη; ICF; Set initial configuration register
            if len(data_bytes)==3:
                ICF = get_16bit(data_bytes) #1st bit never high
                dICF = analyze_ICFG(ICF)
                results.update(dICF)
        elif message_id == "DE":  # BLCη; BLC; Set backlash compensation value η
            if len(data_bytes) == 3:
                backlash = get_16bit(data_bytes)
                if backlash < 0:
                    backlash = (1 << 16) + backlash
                results.update({"backlash": backlash})
        else: # CURn; ENA; MCSn; OFF;
            acr, ena, direction, mcs = analyze_message_id(int(message_id,16))
            results.update({"acr": acr, "ena": ena, "direction": direction, "mcs": mcs})
            # analyze data, 1st byte CUR, 2-4 set SPD, 5-9 QEC
            if len(data_bytes) == 9: #all messages should return 9 data bytes
                sCur = get_current(data_bytes[0]) #set current
                sSpd = get_16bit(data_bytes[1:4]) #actual speed
                rDisplacement = get_32bit(data_bytes[4:]) #actual displacement
                results.update({"sCur": sCur, "sSpd": sSpd, "rDisplacement": rDisplacement})
    elif header == "CC":  # Feedback-Header "CC"
        if message_id == "AD":  # gORG; Set zero/origin position 
            pass
        elif message_id == 'B0': #POS; Check current quadrature encoder’s position for stepper without encoder (one rotaion 3200)
            if len(data_bytes) == 5:
                rEncoder = get_32bit(data_bytes)
                results.update({"rEncoder": rEncoder})
        elif message_id == "B1":  # QEC; Check current quadrature encoder’s position for stepper with encoder (one rotaion 2000)
            if len(data_bytes) == 5: #all messages should return 5 data bytes
                rEncoder = get_32bit(data_bytes) #actual encoder position
                results.update({"rEncoder": rEncoder})
        elif message_id == "B2":  # SPD; Check current speed
            if len(data_bytes) == 3:
                rSpd = get_16bit(data_bytes)
                results.update({"rSpd": rSpd})
        elif message_id == "B3":  # STP; Check current incremental displacement
            if len(data_bytes) == 5: #all messages should return 5 data bytes
                rDisplacement = get_32bit(data_bytes) #set encoder position
                results.update({"rDisplacement": rDisplacement})
        elif message_id == "C1":  # SFB; Check sensor status
            if len(data_bytes) == 5:
                statusS1=data_bytes[0]
                statusS2=data_bytes[1]
                statusS3=data_bytes[2]
                analogStatus = get_16bit(data_bytes[3:])
                results.update({"S1": statusS1,"S2": statusS2,"S3": statusS3,"AnalogIn": analogStatus})
        elif message_id == "DE":  # MDL; Check the model of controller
            pass #not implemented
        elif message_id == "A0": #falling edge on S1, only works if RTCN action is configured
            results.update({"S1": 0})
        elif message_id == "A1": #rising edge on S1
            results.update({"S1": 1})
        elif message_id == "A2": #falling edge on S2
            results.update({"S2": 0})
        elif message_id == "A3": #rising edge on S2
            results.update({"S2": 1})
        elif message_id == "A4": #falling edge on S3
            results.update({"S3": 0})
        elif message_id == "A5": #rising edge on S3
            results.update({"S3": 1})
        elif message_id == "A6":
            pass #not implemented
        elif message_id == "A7":
            pass #not implemented
        elif message_id == "A8":
            if len(data_bytes) == 6: #all messages should return 6 data bytes
                unknown = get_current(data_bytes[0]) #unkown value, not documented
                rEncoder = get_32bit(data_bytes[1:]) #actual encoder position
                results.update({"rEncoder": rEncoder})
        elif message_id == "A9":
            pass
        else: # FBK;
            acr, ena, direction, mcs = analyze_message_id(int(message_id,16))
            results.update({"acr": acr, "ena": ena, "direction": direction, "mcs": mcs})
            if len(data_bytes) == 9: #all messages should return 9 data bytes
                rCur = get_current(data_bytes[0]) #set current
                rSpd = get_16bit(data_bytes[1:4]) #actual speed
                rDisplacement = get_32bit(data_bytes[4:]) #actual encoder position
                results.update({"rCur": rCur, "rSpd": rSpd, "rDisplacement": rDisplacement})
            # analyze data, 1st byte CUR, 2-4 actual SPD, 5-9 position(?)
    elif header == "EE":  # Feedback-Header "EE" für Fehler
        # Aktionen für Fehlerfälle hier implementieren...
        pass
    else:
        pass
    return results

def get_message(data):

    if len(data) < 4:
        raise ValueError(f"Invalid message length: {len(data)}")
    
    # Header
    header = hex(data[0])[2:].upper()  # Header als Hexadezimalwert
    # Controller ID
    controller_id = data[1]  # Controller ID als Zahl
    # Message ID
    message_id = hex(data[2])[2:].upper()  # Message ID als Zahl
    # Terminator
    terminator = hex(data[-1])[2:].upper()  # Terminator als Hexadezimalwert
    data_bytes = data[3:-1]  # Datenbytes ohne Header, Controller ID, Message ID und Terminator
    return header, controller_id, message_id, data_bytes, terminator

def get_32bit(data_bytes):
    data_value=0
    data_value |= (data_bytes[0] & 0x000F) << 28  # D31-D28
    data_value |= (data_bytes[1] & 0x7F) << 21   # D27-D21
    data_value |= (data_bytes[2] & 0x7F) << 14   # D20-D14
    data_value |= (data_bytes[3] & 0x7F) << 7   # D13-D7
    data_value |= data_bytes[4]                # D6-D0
    if data_value & 0x80000000:
        data_value = -((data_value ^ 0xFFFFFFFF) + 1)
    return data_value

def get_16bit(data_bytes):
    while len(data_bytes) < 3:
        data_list = list(data_bytes)
        data_list.insert(0, 0)
        data_bytes = bytes(data_list)
    data_value=0
    data_value |= (data_bytes[0] & 0x03) << 14  # D15-D14
    data_value |= (data_bytes[1] & 0x7F) << 7   # D13-D7
    data_value |= data_bytes[2]                # D6-D0
    if data_value & 0x8000:
        data_value = -((data_value ^ 0xFFFF) + 1)
    return data_value

def analyze_MCFG(value):
    # Bitmasken für die einzelnen Bits
    ANE_MASK    = 0b1000000000000000
    CHS_MASK    = 0b0100000000000000
    QEI_MASK    = 0b0010000000000000
    QEM_MASK    = 0b0000100000000000
    CM_MASK     = 0b0000010000000000
    AM_MASK     = 0b0000001000000000
    DM_MASK     = 0b0000000100000000
    STLIE_MASK  = 0b0000000001000000
    ORGIE_MASK  = 0b0000000000100000
    STPIE_MASK  = 0b0000000000010000
    P4IE_MASK   = 0b0000000000001000
    S3IE_MASK   = 0b0000000000000100
    S2IE_MASK   = 0b0000000000000010
    S1IE_MASK   = 0b0000000000000001
    # Auswerten der einzelnen Bits
    ANE = bool(value & ANE_MASK)
    CHS = bool(value & CHS_MASK)
    QEI = bool(value & QEI_MASK)
    QEM = bool(value & QEM_MASK)
    CM = bool(value & CM_MASK)
    AM = bool(value & AM_MASK)
    DM = bool(value & DM_MASK)
    STLIE = bool(value & STLIE_MASK)
    ORGIE = bool(value & ORGIE_MASK)
    STPIE = bool(value & STPIE_MASK)
    P4IE = bool(value & P4IE_MASK)
    S3IE = bool(value & S3IE_MASK)
    S2IE = bool(value & S2IE_MASK)
    S1IE = bool(value & S1IE_MASK)
    results={
        "ANE": ANE,
        "CHS": CHS,
        "QEI": QEI,
        "QEM": QEM,
        "CM": CM,
        "AM": AM,
        "DM": DM,
        "STLIE": STLIE,
        "ORGIE": ORGIE,
        "STPIE": STPIE,
        "P4IE": P4IE,
        "S3IE": S3IE,
        "S2IE": S2IE,
        "S1IE": S1IE
    }
    # Ergebnis zurückgeben
    return results

def get_current(byte):
    current=byte/10
    return current

def analyze_ICFG(value):
    # Bitmasken für die einzelnen Bits
    Elock_MASK   = 0b0000000000001000
    #PROG_MASK   = 0b0000000000000100
    CCW_MASK   = 0b0000000000000010
    ENA_MASK   = 0b0000000000000001
    # Auswerten der einzelnen Bits
    P4IE = bool(value & Elock_MASK)
    #S3IE = bool(value & PROG_MASK)
    S2IE = bool(value & CCW_MASK)
    S1IE = bool(value & ENA_MASK)
    results={
        "Elock": P4IE,
        #"PROG": S3IE,
        "CCW": S2IE,
        "autoENA": S1IE
    }
    # Ergebnis zurückgeben
    return results

def analyze_message_id(message_id):
    # Extrahiere die Bits entsprechend den angegebenen Regeln
    acr_bit = (message_id & 0x40) >> 6
    ena_bit = (message_id & 0x20) >> 5
    dir_bit = (message_id & 0x10) >> 4
    mcs_bits = message_id & 0x0F #0: "Full Step", 1: "1/2 Step",3: "1/4 Step", 7: "1/8 Step", 15: "1/16 Step"
    steps_lookup = {0: 1, 1: 2, 3: 4, 7: 8, 15: 16}
    mcs_steps = steps_lookup.get(mcs_bits, None)
    return acr_bit, ena_bit, dir_bit, mcs_steps