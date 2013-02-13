import httplib2

class NetworkCommunicator(object):

    NETWORK_TIMEOUT = 5 #in seconds

    def __init__(self, bridge_address):
        self.BridgeAddress = bridge_address
        
    def GetRequest(self, command):
        return self.Request(command, "GET")
        
    def PutRequest(self, command, data):
        return self.Request(command, "PUT", data, {'content-type':'application/json'})

    def PostRequest(self, command, data):
        return self.Request(command, "POST", data, {'content-type':'application/json'})
        
    def Request(self, command, request_method, request_body = None, request_headers = None):
        response = None
        content = None
    
        http = httplib2.Http(timeout = self.NETWORK_TIMEOUT)
        response, content = http.request(self.BridgeAddress + "/" + command, method = request_method, body = request_body, headers = request_headers)

        #print "Response: %s" % (response)
        #print "Content: %s" % (content)
       
        if response['status'] != '200':
            raise Exception(response)
        
        return content
    