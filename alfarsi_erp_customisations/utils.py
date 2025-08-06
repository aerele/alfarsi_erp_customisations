def build_soap_request_client_info(client_info: dict) -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
			   xmlns:v1="http://ws.aramex.net/ShippingAPI/v1/">
  <soap:Body>
	<v1:CountriesFetchingRequest>
	  <v1:ClientInfo>
		<v1:UserName>{client_info["UserName"]}</v1:UserName>
		<v1:Password>{client_info["Password"]}</v1:Password>
		<v1:Version>{client_info.get("Version", "v1.0")}</v1:Version>
		<v1:AccountNumber>{client_info["AccountNumber"]}</v1:AccountNumber>
		<v1:AccountPin>{client_info["AccountPin"]}</v1:AccountPin>
		<v1:AccountEntity>{client_info["AccountEntity"]}</v1:AccountEntity>
		<v1:AccountCountryCode>{client_info["AccountCountryCode"]}</v1:AccountCountryCode>
	  </v1:ClientInfo>
	</v1:CountriesFetchingRequest>
  </soap:Body>
</soap:Envelope>"""
