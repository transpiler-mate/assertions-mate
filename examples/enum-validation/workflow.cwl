# Copyright 2025 Terradue
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

cwlVersion: v1.2

$namespaces:
  s: https://schema.org/
'@type': s:SoftwareApplication
s:name: 'My shiny workflow'
s:description: 'There is no workflow on earth like this one that solves NP-complete problems.'
s:dateCreated: '2025-01-01'
s:license:
  '@type': s:CreativeWork
  s:identifier: CC-BY-4.0
  s:name: 'Creative Commons Attribution 4.0 International'
  s:url: https://spdx.org/licenses/CC-BY-4.0.html
s:identifier: 10.5072/zenodo.393958
s:sameAs: https://handle.test.datacite.org/10.5072/zenodo.393958
s:keywords:
  - CWL
  - Workflow
  - 'Earth Observation'
  - '@type': s:DefinedTerm
    s:name: application-type
    s:description: delineation
  - '@type': s:DefinedTerm
    s:name: domain
    s:description: hydrology
  - '@type': s:DefinedTerm
    s:name: 'SURFACE WATER FEATURES'
    s:description: 'EARTH SCIENCE > TERRESTRIAL HYDROSPHERE > SURFACE WATER > SURFACE WATER FEATURES'
    s:termCode: 959f1861-a776-41b1-ba6b-d23c71d4d1eb
    s:inDefinedTermSet: https://cmr.earthdata.nasa.gov/kms/concepts/concept_scheme/sciencekeywords
s:softwareRequirements:
  - https://cwltool.readthedocs.io/en/latest/
  - https://www.python.org/
s:softwareVersion: 3.0.0
s:softwareHelp:
  - '@type': s:CreativeWork
    s:name: 'User Manual'
    s:url: https://meoga-shiny-workflow.readthedocs.io/en/latest/
  - '@type': s:CreativeWork
    s:name: 'Admin Manual'
    s:url: https://meoga.io/meoga/shiny-workflow/admin
s:publisher:
  '@type': s:Organization
  s:name: 'Make Earth Observation Great Again'
  s:email: 'info@meoga.com'
  s:identifier: https://ror.org/9999cx000
s:author:
  - '@type': s:Role
    s:roleName: Conceptualization
    s:startDate: '2025-01-01'
    s:additionalType: https://credit.niso.org/contributor-roles/conceptualization/
    s:author:
      '@type': s:Person
      s:givenName: Lex
      s:familyName: Luthor
      s:email: 'lex.luthor@luthorcorp.com'
      s:identifier: https://orcid.org/0000-9999-0000-9999
      s:affiliation:
        '@type': s:Organization
        s:name: 'Luthor Corp'
        s:identifier: https://ror.org/0000cx000
s:contributor:
  - '@type': s:Role
    s:roleName: 'Writing – review & editing'
    s:additionalType: https://credit.niso.org/contributor-roles/writing-review-editing/
    s:contributor:
      '@type': s:Person
      s:givenName: Clark
      s:familyName: Kent
      s:email: 'clark.kent@dailyplanet.com'
      s:identifier: https://orcid.org/0000-9999-0000-9999
      s:affiliation:
        '@type': s:Organization
        s:name: 'Daily Planet'
        s:identifier: https://ror.org/0000cx000

$graph:
  - class: Workflow
    id: enum-validation
    inputs:
      mode:
        type: string
    outputs: {}
    steps: {}
    hints:
      - class: eoap:JSONSchemaHint
        json_schema:
          type: object
          required: [mode]
          properties:
            mode:
              type: string
              enum: [fast, strict]
