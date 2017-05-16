from lxml import etree

class XmlIntruder(object):
    def __init__(self, xmlstr):
        self.xml = xmlstr
        self.tree = etree.fromstring(self.xml)

    def gettree(self):
        return self.tree

    def settree(self, str):
        self.tree = etree.fromstring(str)
        return self

    def subtree(self, path):
        tree = self.gettree().xpath(path)
        return tree

    def replace(self, path, xmlstr):
        return self

    def insertBefore(self, path, parentElement):
        return ''

    def insertAfter(self, path, xmlstr):
        return ''
    
    def insertInto(self, path, element, pos=0):
        for e in self.subtree(path):
            e.insert(pos, element)
        return self

    def delete(self, path):
        for e in self.subtree(path):
            if(e.getparent()):
                e.getparent().remove(e)
        return self

    def getAttribs(self, elem):
        return elem.attrib

    def getAttrib(self, elem, name):
        return self.getAttribs(elem)[name]

    def setAttrib(self, elem, name, value):
        self.getAttribs(elem)[name] = value
        return self

    def deleteAttrib(self, elem, name):
        self.getAttribs(elem).pop(name, None)
        return self

    def deleteAllAttrib(self, elem):
        for a in self.getAttribs(elem):
            self.deleteAttrib(elem, a)
        return self

    def addAttrib(self, elem, name, value):
        self.setAttrib(elem, name, value)
        return self

    def addAllAttribs(self, elem, attribs):
        for a in attribs:
            self.addAttrib(elem, a, attribs[a])
        return self

    def write(self, path):
        self.gettree().getroottree().write(path)