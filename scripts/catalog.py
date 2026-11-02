"""Election inventory only. No candidates, votes or winners are seeded."""
STATES = '''AL|Alabama|7
AK|Alaska|1
AZ|Arizona|9
AR|Arkansas|4
CA|California|52
CO|Colorado|8
CT|Connecticut|5
DE|Delaware|1
FL|Florida|28
GA|Georgia|14
HI|Hawaii|2
ID|Idaho|2
IL|Illinois|17
IN|Indiana|9
IA|Iowa|4
KS|Kansas|4
KY|Kentucky|6
LA|Louisiana|6
ME|Maine|2
MD|Maryland|8
MA|Massachusetts|9
MI|Michigan|13
MN|Minnesota|8
MS|Mississippi|4
MO|Missouri|8
MT|Montana|2
NE|Nebraska|3
NV|Nevada|4
NH|New Hampshire|2
NJ|New Jersey|12
NM|New Mexico|3
NY|New York|26
NC|North Carolina|14
ND|North Dakota|1
OH|Ohio|15
OK|Oklahoma|5
OR|Oregon|6
PA|Pennsylvania|17
RI|Rhode Island|2
SC|South Carolina|7
SD|South Dakota|1
TN|Tennessee|9
TX|Texas|38
UT|Utah|4
VT|Vermont|1
VA|Virginia|11
WA|Washington|10
WV|West Virginia|2
WI|Wisconsin|8
WY|Wyoming|1'''
SENATE = set('AL AK AR CO DE GA ID IL IA KS KY LA ME MA MI MN MS MT NE NH NJ NM NC OK OR RI SC SD TN TX VA WV WY'.split())
GOVERNORS = set('AL AK AZ AR CA CO CT FL GA HI ID IL IA KS ME MD MA MI MN NE NV NH NM NY OH OK OR PA RI SC SD TN TX VT WI WY'.split())

def seed():
    states, races = [], []
    def race(state, office, seat, label, special=False):
        races.append(dict(id=f'{state}-{office}-{seat}', state=state, office=office,
                          label=label, special=special, official=None, calls=[], certification=None))
    for line in STATES.splitlines():
        code, name, seats = line.split('|')
        states.append(dict(code=code, name=name))
        for district in range(1, int(seats)+1):
            seat = 'AL' if int(seats) == 1 else f'{district:02}'
            race(code, 'house', seat, 'At-large' if seat == 'AL' else f'District {district}')
        if code in SENATE:
            race(code, 'senate', '2', 'U.S. Senate · Class II')
        if code in ('FL', 'OH'):
            race(code, 'senate', '3-special', 'U.S. Senate · Special election', True)
        if code in GOVERNORS:
            race(code, 'governor', 'general', 'Governor')
    return dict(schemaVersion=1, electionDate='2026-11-03', generatedAt='2026-11-02T18:00:00Z',
                states=states, races=races)
