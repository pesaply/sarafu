# sarafu
Mobile Payment Gateway With API  For Various Telecom Provider ,

#Dependencies


sudo apt-get install subversion git bzr bzrtools python-pip postgresql postgresql-server-dev-9.3 python-all-dev python-dev python-setuptools libxml2-dev libxslt1-dev libevent-dev libsasl2-dev libldap2-dev pkg-config libtiff5-dev libjpeg8-dev libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev liblcms2-utils libwebp-dev tcl8.6-dev tk8.6-dev python-tk libyaml-dev fontconfig

#Database 

RethinkDB makes building and scaling realtime apps dramatically easier


Just Added New Fitures 

commit Changes in 5 10 15 


[![Gitter](https://badges.gitter.im/Hojalab/sarafu.svg)](https://gitter.im/Hojalab/sarafu?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)



To extract the amount received, we can use this regular expression:

Umepokea\W+Tsh\W*([\d\,\.]*\d)

Note: You may also want to take special care to avoid letting someone falsify their payment amount by changing their registered name to “Umepokea Tsh 1,000,000”.

To extract the transaction ID, we can use this regular expression:

kumbukumbu no\W+(\w{8}\.\d{4}\.\w{5,}\b)

While SMS receipt formats are typically relatively stable, mobile money systems sometimes change the format or wording of the receipts.

At this point, your service still doesn’t know which user account should be credited for the payment. (You might be able to figure it out from the payee name and phone number, but that’s unreliable.)

Instead, just store the transaction ID and payment amount in your database, so that it’s available in the next step.
3. Match the payment with the correct user and credit their account

Finally, you need to match the receipt with the correct user of your online service, so you can credit the correct account.

Some mobile money systems, including Tigo Pesa, have systems for businesses that allow customers to enter a reference number for their account when sending a bill payment. But this type of bill payment system is sometimes only available to large businesses. When someone sends money to your phone number, they probably won’t be able to send a reference number.

In this case, you can simply prompt the user to enter the transaction ID in your application, like in the example below:

Tigo-pesa-payments


Scraping data from SMS receipts may not be the cleanest solution for accepting mobile money payments, but sometimes it’s the only solution.
