# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2021 UCLouvain
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Signals connector for acquisition order."""


from .api import AcqOrdersSearch
from ..acq_order_lines.dumpers import AcqOrderLineESDumper


def enrich_acq_order_data(sender, json=None, record=None, index=None,
                          doc_type=None, arguments=None, **dummy_kwargs):
    """Signal sent before a record is indexed.

    :param json: The dumped record dictionary which can be modified.
    :param record: The record being indexed.
    :param index: The index in which the record will be indexed.
    :param doc_type: The document type of the record.
    """
    if index.split('-')[0] == AcqOrdersSearch.Meta.index:

        # NOTES PERFORMING ----------------------------------------------------
        #   We include notes from multiple sources into the AcqOrder ES index
        #   to allow search on each terms of any notes related to this parent
        #   resource :
        #     - AcqOrder self notes.
        #     - related `AcqOrderLine` notes.
        #     - related `AcqReceipt` notes.
        #     - `AcqReceiptLine` notes related to `AcqReceipts`.
        #   So for any notes, we will include a `source` attribute to know the
        #   origin of the note.
        for note in json.get('notes', []):
            note['source'] = {
                'pid': record.pid,
                'type': record.provider.pid_type
            }
        for note, source_class, resource_pid in record.get_related_notes():
            json.setdefault('notes', []).append({
                'type': note['type'],
                'content': note['content'],
                'source': {
                    'pid': resource_pid,
                    'type': source_class.provider.pid_type
                }
            })

        # RELATED ORDER LINES METADATA ----------------------------------------
        json['order_lines'] = [
            order_line.dumps(dumper=AcqOrderLineESDumper())
            for order_line in record.get_order_lines()
        ]

        # ADD OTHERS DYNAMIC KEYS ---------------------------------------------
        json.update({
            'status': record.status,
            'item_quantity': {
                'ordered': record.item_quantity,
                'received': record.item_received_quantity
            },
            'organisation': {
                'pid': record.organisation_pid,
                'type': 'org',
            }
        })