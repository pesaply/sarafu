#!coding=utf-8
from string import Template
import base64
try:
    from hashlib import sha1
except ImportError:
    from sha import new as sha1
TSH = 1000
KSH = 100
USH = 500
USD = 2000
    
RESPONSE_CODE_ACCEPTED = 1
RESPONSE_CODE_DENIED = 2
RESPONSE_CODE_ERROR = 3

    
class SignatureError(Exception): pass
    
class Amount(object):
    def __init__(self, amount, currency):
        self.amount = amount
        self.currency = currency
        
    def amount_as_string(self, exponent=2):
        return '%012d' % ((self.amount*100).to_integral())
    
class sarafuResponse(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)
    
sarafu_URL_EN = 'https://https://cloud.pesaply.com/checkout'
sarafu_URL_RU = 'https://cloud.pesaply.com/callback'
    
class sarafu(object):
    currency_exponent = 2
    
    def __init__(self, sarafu_url, merchant_id, password, acquirer_id, merchant_response_url=None, merchant_response_url2=None):
        self.sarafu_url = sarafu_url
        self.version='1.0.0'
        self.merchant_id = merchant_id
        self.password = password
        self.acquirer_id = acquirer_id
        
        if merchant_response_url is None:
            self.merchant_response_url = 'https://cloud.pesaply.com/sucseeded'
        else:
            self.merchant_response_url = merchant_response_url
        self.merchant_response_url2 = merchant_response_url2
     
    def parse_response(self, post):
        acquirer_id = post.get('AcqID')
        merchant_id = post.get('MerchantID')
        order_id = post.get('OrderID')
        signature = post.get('Signature')
        eci = post.get('ECI')
        ip = post.get('IP')
        country_bin = post.get('CountryBIN')
        country_ip = post.get('CountryIP')
        onus = post.get('ONUS')
        time = post.get('Time')
        otp_phone = post.get('OTPPhone')
        phone_country = post.get('PhoneCountry')
        signature2 = post.get('Signature2')
        response_code = post.get('ResponseCode')
        reason_code = post.get('ReasonCode')
        reason_desc = post.get('ReasonDesc')
        refno = post.get('ReferenceNo')
        auth_code = post.get('AuthCode')
        
        if not self._verify_sig1(signature, order_id):
            raise SignatureError('Signature verification failed')
        
        if not self._verify_sig2(signature2, eci, ip, country_ip, country_bin, onus, time, otp_phone, phone_country):
            raise SignatureError('Signature2 verification failed')
        
        return sarafuResponse(order_id=order_id,
                              response_code=response_code,
                              reason_code=reason_code,
                              reason_desc=reason_desc,
                              refno=refno,
                              auth_code=auth_code,
                              eci=eci,
                              ip=ip,
                              country_bin=country_bin,
                              country_ip=country_ip,
                              onus=onus,
                              time=time,
                              otp_phone=otp_phone,
                              phone_country=phone_country)
        
    def build_order_form(self, order_id, amount, alt_amount=None, text=None, xhtml=False, form_attrs={}):
        return self._build_form(order_id, amount, alt_amount, text=text, xhtml=xhtml, form_attrs=form_attrs)
    
    def _build_form(self, order_id, amount, alt_amount=None, additional_data=None, cardno=None, cardcvv=None, text=None, xhtml=False, form_attrs={}):
        data = {'xhtml': xhtml and '/' or '',
                'input_type': 'text',
                'sarafu_url': _escape(self.sarafu_url, True),
                'version': _escape(self.version, True),
                'merchant_id': _escape(self.merchant_id, True),
                'acquirer_id': _escape(self.acquirer_id, True),
                'merchant_response_url': _escape(self.merchant_response_url, True),
                'merchant_response_url2': _escape(self.merchant_response_url2, True),
                'amount': _escape(amount.amount_as_string(), True),            
                'currency': _escape(amount.currency, True),
                'order_id': _escape(order_id, True),
                'signature_method': _escape('SHA1', True),
                'signature': _escape(self._signature(order_id, amount, alt_amount, additional_data)),
                'capture_flag': 'A',
                'currency_exponent': self.currency_exponent,
                'form_attrs': u' '.join('%s="%s"' % x for x in form_attrs.iteritems())
        }
                    
        form = [Template('<form method="post" action="${sarafu_url}" ${form_attrs}>').substitute(data),
                Template('<input type="${input_type}" name="Version" value="${version}" $xhtml>').substitute(data),
                Template('<input type="${input_type}" name="MerID" value="${merchant_id}" $xhtml>').substitute(data),
                Template('<input type="${input_type}" name="AcqID" value="${acquirer_id}" $xhtml>').substitute(data),
                Template('<input type="${input_type}" name="MerRespURL" value="${merchant_response_url}" $xhtml>').substitute(data),
                Template('<input type="${input_type}" name="PurchaseAmt" value="${amount}" $xhtml>').substitute(data),
                Template('<input type="${input_type}" name="PurchaseCurrency" value="${currency}" $xhtml>').substitute(data),
                Template('<input type="${input_type}" name="OrderID" value="${order_id}" $xhtml>').substitute(data),
                Template('<input type="${input_type}" name="SignatureMethod" value="${signature_method}" $xhtml>').substitute(data),
                Template('<input type="${input_type}" name="Signature" value="${signature}" $xhtml>').substitute(data),
                Template('<input type="${input_type}" name="CaptureFlag" value="${capture_flag}" $xhtml>').substitute(data),
                Template('<input type="${input_type}" name="PurchaseCurrencyExponent" value="${currency_exponent}" $xhtml>').substitute(data),
                
                ]
        
        if self.merchant_response_url2 is not None:
            form.append(Template('<input type="${input_type}" name="MerRespURL2" value="${merchant_response_url2}" $xhtml>').substitute(data))

        if alt_amount is not None:
            form.extend([
                Template('<input type="${input_type}" name="PurchaseAmt2" value="${alt_amount}" $xhtml>').substitute(data, alt_amount=_escape(alt_amount.amount_as_string(), True)),
                Template('<input type="${input_type}" name="PurchaseCurrency2" value="${alt_currency}" $xhtml>').substitute(data, alt_currency=_escape(alt_amount.currency, True)),
            ])
            
        if cardno is not None:
            form.append('<input type="${input_type}" name="CardNo" value="${cardno}" $xhtml>').substitute(data, cardno=cardno)

        if cardcvv is not None:
            form.append('<input type="${input_type}" name="CardCVV2" value="${cardcvv}" $xhtml>').substitute(data, cardcvv=_escape(cardcvv, True))

        if text is not None:
            form.append(Template('<input type="submit" value="$text" $xhtml>').substitute(data, text=_escape(text, True)))
        form.append('</form>')
        
        return u''.join(form)
    
    def _signature(self, order_id, amount, alt_amount=None, additional_data=None):
        s = [self.password, self.merchant_id, self.acquirer_id, order_id, amount.amount_as_string(), amount.currency]
        
        if alt_amount is not None:        
            s.append(alt_amount.amount_as_string())
            s.append(alt_amount.currency)

        if additional_data is not None:
            s.append(additional_data)
            
        return self._build_sig(s)
        
    def _verify_sig1(self, sig, order_id):
        s = [self.password, self.merchant_id, self.acquirer_id, order_id]
        return self._build_sig(s) == sig
    
    def _verify_sig2(self, sig,  eci, ip, country_ip, country_bin, onus, time, otp_phone, phone_country):
        return self._build_sig([eci, ip, country_ip, country_bin, onus, time, otp_phone, phone_country]) == sig
     
    @classmethod 
    def _build_sig(cls, token_list):
        token_list = [str(x) for x in token_list]
        s = ''.join(token_list)
        digest = sha1(s).digest()
        return base64.encodestring(digest).strip()
        
def _escape(s, quote=False):
    """Ripped from Werkzeug
    Replace special characters "&", "<" and ">" to HTML-safe sequences.  If
    the optional flag `quote` is `True`, the quotation mark character (") is
    also translated.

    There is a special handling for `None` which escapes to an empty string.

    :param s: the string to escape.
    :param quote: set to true to also escape double quotes.
    """
    if s is None:
        return ''
    elif hasattr(s, '__html__'):
        return s.__html__()
    elif not isinstance(s, basestring):
        s = unicode(s)
    s = s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    if quote:
        s = s.replace('"', "&quot;")
    return s
        
