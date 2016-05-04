import jnettool.tool.elements.NetworkElements
import jnettool.tool.Routing
import jnettool.tool.RouteInspector
    ne = jnettool.tools.elements.NetworkElements('ip')
	try
	   routing_tableb = ne.getRoutingTable()
	except jnettool.tools.elements.MissingVar:
	   logging.exception('No routing_tableb found')
	   ne.cleanup('rollback')
	   
	else
	   num_routes =routing_table.getSize()
	   for RToffset in range (num_routes):
	   route = routing_table.getRouteByIndex(RToffset)
	   name = route.getName()
	   ipaddr = route.get.IPAddr()
	   print "$15s -> %s" %  (name ipaddr)
	finally
	   ne.cleanup ('commit')
	   ne.dissconnect()
##########################################################
from nettools import NetworkElements

with NetworkElements ('IP') as ne:
    for route in ne.routing_table:
	print "$15s -> %s" % (route.name route.ipaddr)

class NetworkElements (Exception):
pass
	
	class NetworkElements (object)"
	
def __init__(self , ipaddr):
    self.oldne == jnettool.tools.NetworkElements ()  
class
