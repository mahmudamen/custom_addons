/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useEffect } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { kanbanView } from "@web/views/kanban/kanban_view";

export class RoomKanbanController extends KanbanController {
    setup() {
        super.setup();

        useEffect(() => {
            this._styleKanbanCards();
        });
    }

    _styleKanbanCards() {
        // Add styling attributes to kanban cards
        const records = document.querySelectorAll('.o_kanban_record');
        records.forEach(record => {
            const roomType = record.querySelector('[name="room_type"]');
            const roomCapacity = record.querySelector('[name="room_capacity"]');
            const isAvailable = record.querySelector('[name="is_available"]');

            if (roomType) {
                record.setAttribute('data-type', roomType.textContent.trim().toLowerCase());
            }

            if (roomCapacity) {
                record.setAttribute('data-capacity', roomCapacity.textContent.trim().toLowerCase());
            }

            if (isAvailable) {
                const value = isAvailable.textContent.trim().toLowerCase();
                if (value === 'true' || value === 'available') {
                    record.setAttribute('data-status', 'available');
                } else {
                    record.setAttribute('data-status', 'full');
                }

                // Add status badge if not exists
                if (!record.querySelector('.room-status')) {
                    const statusDiv = document.createElement('div');
                    statusDiv.className = `room-status ${value === 'true' || value === 'available' ? 'available' : 'occupied'}`;
                    statusDiv.textContent = value === 'true' || value === 'available' ? 'Available' : 'Occupied';

                    const titleEl = record.querySelector('.o_kanban_record_top');
                    if (titleEl) {
                        titleEl.appendChild(statusDiv);
                    }
                }
            }

            // Style patient count
            const patientCount = record.querySelector('div:last-child span');
            if (patientCount) {
                const count = parseInt(patientCount.textContent.trim());
                if (count === 0) {
                    patientCount.classList.add('available');
                } else {
                    patientCount.classList.add('occupied');
                }
            }
        });
    }

    /**
     * @override
     */
    async onGlobalClick(ev) {
        // Add styling after any update
        setTimeout(() => this._styleKanbanCards(), 100);
        return super.onGlobalClick(ev);
    }
}

registry.category("views").add("hospital_rooms_kanban", {
    ...kanbanView,
    Controller: RoomKanbanController,
});