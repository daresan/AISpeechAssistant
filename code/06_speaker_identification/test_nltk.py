import re
import nltk; nltk.download('punkt_tab')
import pyperclip

# Download NLTK data if needed


def split_text(text):
    paragraphs = text.split('\r\n')
    sentences = []

    for para in paragraphs:
        # Find all hyperlinks using a regular expression
        hyperlinks = re.findall(r'\bhttps?://\S+', para)

        # Tokenize the paragraph into sentences
        tokens = nltk.sent_tokenize(para)

        for token in tokens:
            # Check if the token contains a hyperlink and adjust accordingly
            for hyperlink in hyperlinks:
                if hyperlink in token:
                    # Handle cases where the hyperlink is split across multiple tokens
                    # ... (implementation depends on specific requirements)
                    break
            else:
                sentences.append(token)

    return sentences

# Example usage
#text = "Der Autor:\r\nJonas Freiknecht, Landau\r\nwww.jofre.de\r\nAlle in diesem Werk enthaltenen Informationen, Verfahren und Darstellungen wurden nach bestem Wissen zusammengestellt und mit Sorgfalt geprüft und getestet. Dennoch sind Fehler nicht ganz auszuschließen. Aus diesem Grund sind die im vorliegenden Werk enthaltenen Informationen mit keiner Verpflichtung oder Garantie irgendeiner Art verbunden. Autor und Verlag übernehmen infolgedessen keine Verantwortung und werden keine daraus folgende oder sonstige Haftung übernehmen, die auf irgendeine Weise aus der Benutzung dieser Informationen – oder Teilen davon – entsteht.\r\nEbenso wenig übernehmen Autor und Verlag die Gewähr dafür, dass die beschriebenen Verfahren usw. frei von Schutzrechten Dritter sind. Die Wiedergabe von Gebrauchsnamen, Handelsnamen, Warenbezeichnungen usw. in diesem Werk berechtigt also auch ohne besondere Kennzeichnung nicht zu der Annahme, dass solche Namen im Sinne der Warenzeichen- und Markenschutz-Gesetzesgebung als frei zu betrachten wären und daher von jedermann benutzt werden dürften. Bibliografische Information der Deutschen Nationalbibliothek:\r\nDie Deutsche Nationalbibliothek verzeichnet diese Publikation in der Deutschen Nationalbibliografie; detaillierte bibliografische Daten sind im Internet über http://dnb.d-nb.de abrufbar. Dieses Werk ist urheberrechtlich geschützt.\r\nAlle Rechte, auch die der Übersetzung, des Nachdruckes und der Vervielfältigung des Werkes, oder Teilen daraus, vorbehalten. Kein Teil des Werkes darf ohne schriftliche Einwilligung des Verlages in irgendeiner Form (Fotokopie, Mikrofilm oder ein anderes Verfahren), auch nicht für Zwecke der Unterrichtsgestaltung – mit Ausnahme der in den §§ 53, 54 URG genannten Sonderfälle –, reproduziert oder unter Verwendung elektronischer Systeme verarbeitet, vervielfältigt oder verbreitet werden.\r\n© 2023 Carl Hanser Verlag GmbH & Co. KG, München, http://www.hanser-fachbuch.de\r\nLektorat: Sylvia Hasselbach\r\nCopy editing: Walter Saumweber, Ratingen\r\nCoverkonzept: Marc Müller-Bremer, München, www.rebranding.de\r\nCovergestaltung: Max Kostopoulos\r\nTitelmotiv: gettyimages.de/CHRISTOPH BURGSTEDT/SCIENCE PHOTO LIBRARY\r\nSatz: Manuela Treindl, Fürth\r\nDruck und Bindung: Hubert & Co. GmbH & Co. KG BuchPartner, Göttingenn\r\nPrinted in Germany\r\nPrint-ISBN: 978-3-446-47231-0\r\nE-Book-ISBN: 978-3-446-47448-2\r\nE-Pub-ISBN: 978-3-446-47659-2\r\n"
input('Warte auf Text')
text = pyperclip.paste()
result = split_text(text)
for sentence in result:
    sentence = sentence.strip()
    print(sentence)
