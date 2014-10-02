#people.py

#!/usr/bin/env python

# A person, with name, aliases, and email address.
class Person:
    def __init__(self, name):
        self.aliases = set()
        self.emails = set()

        # Set the canonical name for this person.  Also add it as an
        # alias, so we don't have to special-case it in the future.
        self.name = name
        self.aliases.add(name)

    def __str__(self):
        return self.name + ' ' + str(self.aliases) + ' ' + str(self.emails)

    # Define equality as having either at least one alias or at least
    # one email address in common.  Or, if we're comparing to a
    # string, define equality as that string being either an alias or
    # an email address.
    def __eq__(self, other):
        try:
            if self.aliases.isdisjoint(other.aliases) and \
               self.emails.isdisjoint(other.emails):
                return False
            else:
                return True
        except:
            if other in self.aliases or other in self.emails:
                return True
            else:
                return False

    # Bogus hash function to make sets work.  A unity hash like this
    # is super-inefficient, but we're only dealing with small sets of
    # names, so we can live with it.
    def __hash__(self):
        return 1
        
    def addName(self, name):
        self.aliases.add(name)

    def addNames(self, names):
        for name in names:
            self.addName(name)

    def addEmail(self, email):
        self.emails.add(email)

    def addEmails(self, emails):
        for email in emails:
            self.addEmail(email)

    def merge(self, other):
        self.aliases |= other.aliases
        self.emails |= other.emails

# Sets of people.  This is a thin wrapper around a set that gives us
# some extra functionality.
class PersonSet:
    def __init__(self):
        self.people = set()

    def __str__(self):
        s = ''
        for person in self.people:
            # unicode encoding
            # s += '%s' % unicode(person) + '\n'
            s += str(person) + '\n'
        return s

    def __len__(self):
        return len(self.people)
    
    def add(self, person):
        for p in self.people:
            if p == person:
                p.merge(person)
                return
        self.people.add(person)

    def find(self, person):
        for p in self.people:
            if p == person:
                return p
        return None
    

if __name__ == '__main__':
    people = PersonSet()

    p1 = Person('one')
    p1.addName('wun')
    p1.addEmails(['one@foo.com', '1@2.3'])

    p2 = Person('two')
    p2.addEmail('one@foo.com')
    
    people.add(p1)
    people.add(p2)

    print people
    
    print people.find(p2)
    print people.find('1@2.3')
