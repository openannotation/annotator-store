from elixir import *

class Annotation(Entity):
    id = Field(Integer, primary_key=True)
    text = Field(UnicodeText)
    ranges = OneToMany('Range')

    def from_dict(self, data):
        if u'ranges' in data:
            ranges = data[u'ranges']
            del data[u'ranges']

        super(Annotation, self).from_dict(data)

        for range_data in ranges:
            if u'id' in range_data:
                range = Range.get(range_data[u'id'])
            else:
                range = Range()

            range.from_dict(range_data)
            self.ranges.append(range)

    def to_dict(self, deep={}, exclude=[]):
        deep.update({'ranges': {}})

        return super(Annotation, self).to_dict(deep, exclude)

    def __repr__(self):
        return '<Annotation %s>' % (self.id)

class Range(Entity):
    id          = Field(Integer, primary_key=True)
    start       = Field(Unicode(255))
    end         = Field(Unicode(255))
    startOffset = Field(Integer)
    endOffset   = Field(Integer)

    annotation  = ManyToOne('Annotation')

    def __repr__(self):
        return '<Range %s>' % (self.id)
