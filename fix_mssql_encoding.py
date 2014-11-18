#!/usr/bin/python
# -*- coding: latin-1 -*-
# fix_mssql_encoding.py
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
# Author: Niels Kjøller Hansen <niha07@frederiksberg.dk>
# Copyright: Frederiksberg Kommune

"""Program til at oversætte en database-tabel fra fejl-encodet utf-8 til rigtig latin1
 Virker umiddelbart for danske specialtegn."""

import sys
from osgeo import ogr
from optparse import OptionParser # optparse-modulet bruges til at tage imod
                                  # parametre fra kommandolinjen

# OptParse-opsætning - Defaults er sat op til vores database på Frederiksberg.
parser = OptionParser(usage="usage: %prog [options] tabelnavn")
parser.add_option("-S", "--server", dest="server", default="", help="Database-server")
parser.add_option("-s", "--schema", dest="schema", default="dbo", help="Schemaet, hvor tabellen ligger i")
parser.add_option("-d", "--database", dest="database", default="", help="Navn paa databasen")
parser.add_option("-a", "--auth", dest="auth", default="trusted_connection", help="Autentisering til databasen")
parser.add_option("-q", "--quiet", dest="quiet", action="store_true", default=False, help="Vis ikke output (bortset fra fejl)")
(options, args) = parser.parse_args()
# Hvis ikke der er et tabelnavn, så afslut.
if not args:
    parser.error("Tabelnavn mangler.")
    
# Forbind til database, og hent lag.
ds = ogr.Open('MSSQL:server=%s;database=%s;%s;Tables=%s.%s' % (options.server,options.database,options.auth,options.schema,args[0]), True)
if not ds:
    print "Kunne ikke forbinde til tabel - proev evt at angive et schema."
    sys.exit(1)
lyr = ds.GetLayer(0)
if not lyr:
    print "Kunne ikke forbinde til lag - proev evt at angive et schema."
    sys.exit(1)

# Identificer hvilke felter der er streng-felter
lyr_def = lyr.GetLayerDefn()
string_fields = {}
for i in range(0,lyr_def.GetFieldCount()):
    if lyr_def.GetFieldDefn(i).GetType() == 4:
        string_fields[i] = lyr_def.GetFieldDefn(i).GetName()
    
# Gennemløb alle rækker, og konverterer tegnsættet
finished = False
count = lyr.GetFeatureCount()
index = 1

# Maybe this isn't necessary, but I probably did for a reason?
features = []
for feature in lyr:
    features.append(feature)

# Run through all features, and translate string fields from utf8 to latin1
for feature in features:
    for string_field in string_fields.values():
        string_content = feature.GetField(string_field)
        try:
            if string_content:
                feature.SetField(string_field,string_content.decode('utf8').encode('latin1'))
        except:
            if not options.quiet: print "Fejl ved konvertering af raekke"
    # Skriver features i databasen
    lyr.SetFeature(feature)
    # Put out progress to terminal (unless quiet)
    if not options.quiet:
        sys.stdout.write("\r%d%%" % (100*index/count))   # or print >> sys.stdout, "\r%d%%" %i,
        sys.stdout.flush()
    index = index+1


if not options.quiet: print "\n\nKonvertering af tegnsaet gennemfoert"
