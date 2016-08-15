"""
pesaply
~~~~~~~~~~~~~~~~~~~~
This is the core module for all the functionality required
to interact with the pesaply Mobile Money web application.
"""
from copy import deepcopy
import csv
from cStringIO import StringIO
from datetime import datetime
from .exceptions import *
import json
import mechanize
import re
import urllib


class pesaplyMM(object):
    """
    Interacting with the pesaply Mobile Money system using this library is
    easy. Simply create an object of this class using the account number and
    pin of the account you wish to interact with and call the methods representing
    the operation you want to carry out.
    Example:
     mm = PS('2550000000', '0000') # where '0000' is the pin
    > transactions = mm.get_transactions()
    It's that simple.
    """
    AUTH_URL = 'https://sarafu.pesaply.com/do/login'
    TRANSACTIONS_EXPORT_URL = 'https://sarafu.pesaply.com/do/exportAccountHistoryToCsv'
    TRANSACTIONS_URL = 'https://sarafu.pesaply.com/do/member/accountHistory?advanced=true&memberId=0&typeId=5'
    SEARCH_MEMBERS_URL = 'https://sarafu.pesaply.com/do/searchMembersAjax'
    MOBILE_WEB_URL = 'https://wap.pesaply.com/%(accountno)s/Bluesarafu'
    ERROR_URL = 'https://sarafu.pesaply.com/do/error'
    TRANSACTIONS_FORM = None

    def __init__(self, account, pin, browser=None):
        """
        In some occasions where you'll make a number of requests
        to the server, you will want to store the mechanize browser
        object in some cache so it can be reused.
        This has the advantage of reducing the number of requests
        necessary to complete given tasks.
        The browser object can simply be created this way:
        > browser = mechanize.Browser()
        """
        self.account = account
        self.pin = pin
        self.br = browser or mechanize.Browser()
        self.br.set_handle_robots(False)

    def get_account_details(self, account):
        """
        This method can be used in a number of scenarios:
        1. When it is necessary to very account information
        2. When there's a need to filter transactions by an account id
        3. When account details (e.g. name of account) are needed
        """
        _form = mechanize.HTMLForm(self.SEARCH_MEMBERS_URL, method="POST")
        _form.new_control('text', 'username', {'value': account})
        _form.new_control('text', '_', {'value': ''})

        try:
            r = self.post_url(self.SEARCH_MEMBERS_URL, form=_form)
        except AuthRequiredException:
            self._auth()
            r = self.post_url(self.SEARCH_MEMBERS_URL, form=_form)

        if r:
            # single quoted json parameters are not valid so convert
            # them into double quoted parameters
            _decoded = json.loads(r.replace("'", '"'))
            # we have a double array result so retrieve only what's
            # essential
            if _decoded[0]:
                return _decoded[0][0]

        raise InvalidAccountException

    def get_transactions(self, **kwargs):
        """
        This method optionally takes the following extra
        keyword arguments:
        to_date: a datetime object representing the date the filter should end with
        from_date: a datetime object representing the date the filter should start from
        txn_ref: the transaction reference of a particular transaction
        from_account_id: the account id for the account to filter transactions by (you will
        need to get this information from `get_account_details` method)
        If you specify txn_ref, then it's not necessary to specify to_date and from_date.
        """
        kw_map = {
            'to_date': 'query(period).end',
            'from_account_id': 'query(member)',
            'from_date': 'query(period).begin',
            'txn_ref': 'query(transactionNumber)'}

        if not self.TRANSACTIONS_FORM:
            try:
                self.get_url(self.TRANSACTIONS_URL)
            except AuthRequiredException:
                self._auth()
                self.get_url(self.TRANSACTIONS_URL)
            self.br.select_form("accountHistoryForm")
            self.br.form.method = 'POST'
            self.br.form.action = self.TRANSACTIONS_EXPORT_URL
            self.TRANSACTIONS_FORM = self.br.form
            _form = deepcopy(self.TRANSACTIONS_FORM)
        else:
            _form = deepcopy(self.TRANSACTIONS_FORM)

        # make all hidden and readonly fields writable
        _form.set_all_readonly(False)

        for key, field_name in kw_map.items():
            if key in kwargs:
                # if the field is a date, format accordingly
                if key.endswith('_date'):
                    _form[field_name] = kwargs.get(key).strftime('%d/%m/%Y')
                else:
                    _form[field_name] = kwargs.get(key)

        try:
            r = self.post_url(self.TRANSACTIONS_EXPORT_URL, form=_form)
            return self._parse_transactions(r)
        except AuthRequiredException:
            self._auth()
            r = self.post_url(self.TRANSACTIONS_EXPORT_URL, form=_form)
            return self._parse_transactions(r)

    def make_payment(self, recipient, amount, description=None):
        """
        make_payment allows for automated payments.
        A use case includes the ability to trigger a payment to a customer
        who requires a refund for example.
        You only need to provide the recipient and the amount to be transfered.
        It supports transfers in Kobo as well, just add the necessary decimals.
        """
        self.br.open(self.MOBILE_WEB_URL % {'accountno': self.account})
        try:
            # Search for the existence of the Register link - indicating a new account
            # Payments cannot be made from an account that isn't registered - obviously.
            self.br.find_link(text='Register')
            raise InvalidAccountException
        except mechanize.LinkNotFoundError:
            pass

        # Follow through by clicking links to get to the payment form
        self.br.follow_link(text='My sarafu')
        self.br.follow_link(text='Transfer')
        self.br.follow_link(text='sarafu-to-sarafu')
        self.br.select_form(nr=0)
        self.br['recipient'] = recipient
        self.br.new_control('text', 'pin', attrs={'value': self.pin})
        self.br.new_control('text', 'amount', attrs={'value': amount})
        self.br.new_control('text', 'channel', attrs={'value': 'WAP'})
        r = self.br.submit()

        # Right away, we can tell if the recipient doesn't exist and raise an exception
        if re.search(r'Recipient not found', r):
            raise InvalidAccountException

        self.br.select_form(nr=0)
        self.br.new_control('text', 'pin', attrs={'value': self.pin})
        r = self.br.submit().read()

        # We don't get to know if our pin was valid until this step
        if re.search(r'Invalid PIN', r):
            raise AuthDeniedException

        # An error could occur for other reasons
        if re.search(r'Error occured', r):
            raise RequestErrorException

        # If it was successful, we extract the transaction id and return that
        if re.search(r'Transaction id: (?P<txnid>\d+)', r):
            match = re.search(r'Transaction id: (?P<txnid>\d+)', r)
            return match.group('txnid')

    def get_balance(self):
        """
        Retrieves the balance for the configured account
        """
        self.br.open(self.MOBILE_WEB_URL % {'accountno': self.account})
        try:
            # Search for the existence of the Register link - indicating a new account
            self.br.find_link(text='Register')
            raise InvalidAccountException
        except mechanize.LinkNotFoundError:
            pass

        self.br.follow_link(text='My sarafu')
        self.br.follow_link(text='Balance Inquiry')
        self.br.select_form(nr=0)
        self.br['pin'] = self.pin
        r = self.br.submit().read()

        # Pin valid?
        if re.search(r'Invalid PIN', r):
            raise AuthDeniedException

        # An error could occur for other reasons
        if re.search(r'Error occured', r):
            raise RequestErrorException

        # If it was successful, we extract the balance
        if re.search(r'Your balance is TSH (?P<balance>[\d\.]+)', r):
            match = re.search(r'Your balance is TSH (?P<balance>[\d\.]+)', r)
            return match.group('balance')

    def _auth(self):
        _form = urllib.urlencode({'principal': self.account, 'password': self.pin})
        self.br.open(self.AUTH_URL, _form)

        # a successful login response yields a 302 found status code
        # and a redirect location of https://sarafu.pesaply.com/do/member/home
        if self.br.geturl().startswith(self.ERROR_URL):
            raise AuthDeniedException
        else:
            return True

    def get_url(self, url):
        """
        Internally used to retrieve the contents of a URL
        """
        _r = self.br.open(url)

        # check that we've not been redirected to the login page
        if self.br.geturl().startswith(self.AUTH_URL):
            raise AuthRequiredException
        elif self.br.geturl().startswith(self.ERROR_URL):
            raise RequestErrorException
        else:
            return _r.read()

    def post_url(self, url, form):
        """
        Internally used to retrieve the contents of a URL using
        the POST request method.
        The `form` parameter is a mechanize.HTMLForm object
        This method will use a POST request type regardless of the method
        used in the `form`.
        """
        _r = self.br.open(url, form.click_request_data()[1])

        # check that we've not been redirected to the login page or an error occured
        if self.br.geturl().startswith(self.AUTH_URL):
            raise AuthRequiredException
        elif self.br.geturl().startswith(self.ERROR_URL):
            raise RequestErrorException
        else:
            return _r.read()

    def _parse_transactions(self, response):
        """
        This method parses the CSV output in `get_transactions`
        to generate a usable list of transactions that use native
        python data types
        """
        transactions = list()

        if response:
            f = StringIO(response)
            reader = csv.DictReader(f)

            for line in reader:
                txn = {}
                txn['date'] = datetime.strptime(line['Date'], '%d/%m/%Y %H:%M:%S')
                txn['description'] = line['Description']
                txn['amount'] = float(line['Amount'].replace(',', ''))
                txn['reference'] = line['Transaction number']
                txn['sender'] = line['???transfer.fromOwner???']
                txn['recipient'] = line['???transfer.toOwner???']
                txn['currency'] = 'TSH'
                txn['comment'] = line['Transaction type']

                transactions.append(txn)

        return transactions
