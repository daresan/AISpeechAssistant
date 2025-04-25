# Python 3.9.5 (default, May 11 2021, 07:48:02)
# [GCC 10.3.0] on linux
# Type "help", "copyright", "credits" or "license" for more information.

sent = []
i = 0
book = ['Der Autor:\r\nJonas Freiknecht, Landau\r\nwww.jofre.de\r\nAlle in diesem Werk enthaltenen Informationen, Verfahren und Darstellungen wurden nach bestem Wissen zusammengestellt und mit Sorgfalt geprüft und getestet. Dennoch sind Fehler nicht ganz auszuschließen. Aus diesem Grund sind die im vorliegenden Werk enthaltenen Informationen mit keiner Verpflichtung oder Garantie irgendeiner Art verbunden. Autor und Verlag übernehmen infolgedessen keine Verantwortung und werden keine daraus folgende oder sonstige Haftung übernehmen, die auf irgendeine Weise aus der Benutzung dieser Informationen – oder Teilen davon – entsteht.\r\nEbenso wenig übernehmen Autor und Verlag die Gewähr dafür, dass die beschriebenen Verfahren usw. frei von Schutzrechten Dritter sind. Die Wiedergabe von Gebrauchsnamen, Handelsnamen, Warenbezeichnungen usw. in diesem Werk berechtigt also auch ohne besondere Kennzeichnung nicht zu der Annahme, dass solche Namen im Sinne der Warenzeichen- und Markenschutz-Gesetzesgebung als frei zu betrachten wären und daher von jedermann benutzt werden dürften. Bibliografische Information der Deutschen Nationalbibliothek:\r\nDie Deutsche Nationalbibliothek verzeichnet diese Publikation in der Deutschen Nationalbibliografie; detaillierte bibliografische Daten sind im Internet über http://dnb.d-nb.de abrufbar. Dieses Werk ist urheberrechtlich geschützt.\r\nAlle Rechte, auch die der Übersetzung, des Nachdruckes und der Vervielfältigung des Werkes, oder Teilen daraus, vorbehalten. Kein Teil des Werkes darf ohne schriftliche Einwilligung des Verlages in irgendeiner Form (Fotokopie, Mikrofilm oder ein anderes Verfahren), auch nicht für Zwecke der Unterrichtsgestaltung – mit Ausnahme der in den §§ 53, 54 URG genannten Sonderfälle –, reproduziert oder unter Verwendung elektronischer Systeme verarbeitet, vervielfältigt oder verbreitet werden.\r\n© 2023 Carl Hanser Verlag GmbH & Co. KG, München, http://www.hanser-fachbuch.de\r\nLektorat: Sylvia Hasselbach\r\nCopy editing: Walter Saumweber, Ratingen\r\nCoverkonzept: Marc Müller-Bremer, München, www.rebranding.de\r\nCovergestaltung: Max Kostopoulos\r\nTitelmotiv: gettyimages.de/CHRISTOPH BURGSTEDT/SCIENCE PHOTO LIBRARY\r\nSatz: Manuela Treindl, Fürth\r\nDruck und Bindung: Hubert & Co. GmbH & Co. KG BuchPartner, Göttingenn\r\nPrinted in Germany\r\nPrint-ISBN: 978-3-446-47231-0\r\nE-Book-ISBN: 978-3-446-47448-2\r\nE-Pub-ISBN: 978-3-446-47659-2\r\n']
paragraphs = book[0].split('\r\n') 
for para in paragraphs:
    check = para
    if check.find('www.') == -1: # or check.find('https:') == -1:
        sent.append(check)
        i += 1
        print('www gefunden!')
        print(str(i) +'. Paragraph:', check)
    else:
        #print('HIER!')
        # Split Sentences:
        if check.find(".") == -1:
            checks = check.split('.')
            for check in checks:
                sent.append(check)
                print(str(i) +'. Paragraph:', check)
                i += 1
        else: 
            sent.append(check)
    #print(sent)
print(sent)
for sentences in sent:
    print(sentences)
    #for sentence in sentences:
    #    print(sentence)
    print('\r\n')

