
from django.db import models

from mep.common.models import AliasIntegerField, DateRange, Named, Notable


class Person(Notable, DateRange):
    '''Model for people in the MEP dataset'''

    # Identifiers
    mep_id = models.CharField(max_length=255, blank=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255)
    viaf_id = models.URLField(blank=True)

    # Vital statistics
    birth_year = AliasIntegerField(db_column='start_year',
        blank=True, null=True)
    death_year = AliasIntegerField(db_column='end_year',
        blank=True, null=True)

    MALE = 'M'
    FEMALE = 'F'
    SEX_CHOICES = (
        ('', '----'),
        (FEMALE, 'Female'),
        (MALE, 'Male'),
    )
    sex = models.CharField(blank=True, max_length=1, choices=SEX_CHOICES)
    title = models.CharField(blank=True, max_length=255)
    profession = models.ForeignKey('Profession', blank=True, null=True)
    nationalities = models.ManyToManyField('Country', blank=True)
    relations = models.ManyToManyField(
        'self',
        through='Relationship',
        symmetrical=False
    )

    def __repr__(self):
        return '<Person %s>' % self.__dict__

    def __str__(self):
        entry_name = '%s, %s' % (self.last_name, self.first_name)
        return entry_name.strip()

    @property
    def full_name(self):
        return ('%s %s' % (self.first_name, self.last_name)).strip()

    class Meta:
        verbose_name_plural = 'people'


class Country(Named):
    '''Django model for countries'''

    code = models.CharField(max_length=3, blank=True)

    class Meta:
        verbose_name_plural = 'countries'


class Profession(Named, Notable):
    '''Model holder for named professions'''
    pass


class Relationship(models.Model):
    '''Through model for ``Person.relationships``'''
    from_person = models.ForeignKey('Person', related_name='from_person')
    to_person = models.ForeignKey('Person', related_name='to_person')
    relationship_type = models.ForeignKey('RelationshipType')

    def __repr__(self):
        """Custom method to produce a more human useable representation
        than dict in this case
        """

        return ("<Relationship {'from_person': <Person %s>, "
                "'to_person': <Person %s>, 'relationship_type': "
                "<RelationshipType %s>}>") % (self.from_person.full_name,
                                              self.to_person.full_name,
                                              self.relationship_type.name)

    def __str__(self):
        return '%s is a %s to %s.' % (
            self.from_person.full_name,
            self.relationship_type.name,
            self.to_person.full_name
            )


class RelationshipType(Named, Notable):
    '''Stock model for relationship types'''
