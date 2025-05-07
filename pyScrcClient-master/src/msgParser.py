class MsgParser(object):
    """
    A parser for TORCS server messages.
    """

    def __init__(self):
        self.server_out = {
            'angle': 0,
            'curLapTime': 0,
            'damage': 0,
            'distFromStart': 0,
            'distRaced': 0,
            'focus': [],
            'fuel': 0,
            'gear': 0,
            'lastLapTime': 0,
            'opponents': [],
            'racePos': 0,
            'rpm': 0,
            'speedX': 0,
            'speedY': 0,
            'speedZ': 0,
            'track': [],
            'trackPos': 0,
            'wheelSpinVel': [],
            'z': 0
        }

        self.client_out = {
            'accel': 0,
            'brake': 0,
            'clutch': 0,
            'gear': 0,
            'steer': 0,
            'focus': 0,
            'meta': 0
        }

    def parse(self, msg):
        d = {}
        if not msg.startswith('('):
            return d

        s = msg.split('(')
        for i in range(1, len(s)):
            if s[i].find(')') < 0:
                continue
            item = s[i].split(')')
            if len(item) < 1:
                continue
            tag_value = item[0].strip().split(' ', 1)
            if len(tag_value) != 2:
                continue
            tag, value = tag_value
            if tag in self.server_out:
                if isinstance(self.server_out[tag], list):
                    d[tag] = self.parse_list(value)
                else:
                    try:
                        d[tag] = float(value)
                    except ValueError:
                        d[tag] = 0.0
        return d

    def parse_list(self, value_str):
        values = []
        for v in value_str.split():
            try:
                values.append(float(v))
            except ValueError:
                continue
        return values

    def stringify(self, dictionary):
        out = ''
        for k, v in dictionary.items():
            if isinstance(v, list):
                out += f'({k}'
                for item in v:
                    out += f' {item:.6f}'
                out += ')'
            else:
                out += f'({k} {v:.6f})'
        return out

# Standalone function for compatibility
_parser = MsgParser()

def parse_server_str(msg):
    return _parser.parse(msg)
