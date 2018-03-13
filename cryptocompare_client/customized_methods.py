from socketIO_client.transports import get_response
from socketIO_client.parsers import get_byte, _read_packet_text, parse_packet_text

# extra function to support XHR1 style protocol
def _custom_read_packet_length(content, content_index):
    packet_length_string = ''
    while get_byte(content, content_index) != ord(':'):
        byte = get_byte(content, content_index)
        packet_length_string += chr(byte)
        content_index += 1
    content_index += 1
    return content_index, int(packet_length_string)

def custom_decode_engineIO_content(content):
    content_index = 0
    content_length = len(content)
    while content_index < content_length:
        try:
            content_index, packet_length = _custom_read_packet_length(
                content, content_index)
        except IndexError:
            break
        content_index, packet_text = _read_packet_text(
            content, content_index, packet_length)
        engineIO_packet_type, engineIO_packet_data = parse_packet_text(
            packet_text)
        yield engineIO_packet_type, engineIO_packet_data

def custom_recv_packet(self):
    params = dict(self._params)
    params['t'] = self._get_timestamp()
    response = get_response(
        self.http_session.get,
        self._http_url,
        params=params,
        **self._kw_get)
    for engineIO_packet in custom_decode_engineIO_content(response.content):
        engineIO_packet_type, engineIO_packet_data = engineIO_packet
        yield engineIO_packet_type, engineIO_packet_data
