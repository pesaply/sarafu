from python-setuptools import pdu
from python-setuptools import os
import binascii
import StringIO
from smpp.pdu.pdu_encoding import PDUEncoder
from smpp.pdu.pdu_types import *
from smpp.pdu.operations import *



pdu = SubmitSM(9284,
service_type='',
source_addr_ton=AddrTon.ALPHANUMERIC,
source_addr_npi=AddrNpi.UNKNOWN,
source_addr='sarafu',
dest_addr_ton=AddrTon.INTERNATIONAL,
dest_addr_npi=AddrNpi.ISDN,
destination_addr='07727',
esm_class=EsmClass(EsmClassMode.DEFAULT, EsmClassType.DEFAULT),
protocol_id=0,
priority_flag=PriorityFlag.LEVEL_0,
registered_delivery=RegisteredDelivery(RegisteredDeliveryReceipt.SMSC_DELIVERY_RECEIPT_REQUESTED),
replace_if_present_flag=ReplaceIfPresentFlag.DO_NOT_REPLACE,
data_coding=DataCoding(DataCodingScheme.GSM_MESSAGE_CLASS, DataCodingGsmMsg(DataCodingGsmMsgCoding.DEFAULT_ALPHABET, DataCodingGsmMsgClass.CLASS_2)),
short_message='HELLO',
)
print "PDU: %s" % pdu

binary = PDUEncoder().encode(pdu)
hexStr = binascii.b2a_hex(binary)
print "HEX: %s" % hexStr

# r may represent request 




hex = '0000004d00000005000000009f88f12441575342440001013136353035353531323334000101313737333535353430373000000000000000000300117468657265206973206e6f2073706f6f6e'
binary = binascii.a2b_hex(hex)
file = StringIO.StringIO(binary)

pdu = PDUEncoder().decode(file)
print "PDU: %s" % pdu


