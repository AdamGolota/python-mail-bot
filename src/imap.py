import time, email, os, re, base64, quopri

from transliterate import translit

from imapclient import IMAPClient

import bot_requests, config

attachment_dir = 'C:/web_projects/python_mail_bot/attachments/'




# Decodes utf-8 text, sent through imap
def encoded_words_to_text(encoded_words):
    encoded_word_regex = r'=\?{1}.+\?{1}[B|Q]\?{1}(.+)\?{1}='
    encoding_regex = r'=\?{1}(.+)\?{1}([B|Q])\?{1}'
    encoding_match = re.match(encoding_regex, encoded_words)
    if encoding_match :
        charset, encoding = encoding_match.groups()
    else :
        return encoded_words
    encoded_text = "".join(re.findall(encoded_word_regex, encoded_words))
    if encoding is 'B':
        byte_string = base64.b64decode(encoded_text)
    elif encoding is 'Q':
        byte_string = quopri.decodestring(encoded_text)
    return byte_string.decode(charset)


# Extracts attachments form a message
def resend_attachments(msg):
    for part in msg.walk():
        if part.get_content_maintype()=='multipart':
            continue
        if part.get('Content-Disposition') is None:
            continue
        fileName = translit(encoded_words_to_text(part.get_filename()), 'ru', reversed=True)
        fn_reg = r'^(.+)(\.{1}.+$)'
        fileName, ext = re.search(fn_reg, fileName).groups()
        fileName = re.sub(r'[^\w]', "_", fileName)[:17] + ext
        
        if bool(fileName):
            filePath = os.path.join(attachment_dir, fileName)
            with open(filePath,'wb') as f:   
                f.write(part.get_payload(decode=True))
            with open(filePath, 'rb') as f:
                bot_requests.sendDocument(f)
            os.remove(filePath)
        

# Extracts text from a message
def getBody(msg) :
    if msg.is_multipart() :
        return getBody(msg.get_payload(0))
    else :
        return msg.get_payload(None, True)

# MAIN

#Open mailbox
M = IMAPClient(config.host)
M.login(config.mail, config.password)
M.select_folder('INBOX')

if config.idle :
    while True:
        M.idle()
        try: 
            responses = M.idle_check(timeout=600)
        except KeyboardInterrupt:
            break
        M.idle_done()
        if len(responses) > 0 and responses[0][1] == b'EXISTS' :
            num = M.search('UNSEEN')[0]
            msg = M.fetch(num, 'RFC822')[num][b'RFC822']
            raw = email.message_from_bytes(msg)
            body = getBody(raw)
            decoded = body.decode('utf-8')
            if not decoded.isspace() :
                bot_requests.sendMessage(decoded)    
            resend_attachments(raw)
else :
    #Find recent emails
    nums = M.search('SINCE 03-Oct-2018')

    for uid, msg in M.fetch(nums, 'RFC822').items() :
        raw = email.message_from_bytes(msg[b'RFC822'])
        body = getBody(raw)
        decoded = body.decode('utf-8')
        if not decoded.isspace() :
            bot_requests.sendMessage(decoded)    
        resend_attachments(raw)
M.logout()
M.shutdown()