/** @odoo-module **/

import { registry } from "@web/core/registry";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { KanbanRecord } from "@web/views/kanban/kanban_record";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart, onMounted, onWillUpdateProps } from "@odoo/owl";

class PatientFileEnhancedRecord extends KanbanRecord {
    setup() {
        super.setup();
        this.animationService = useService("animation");
    }

    async onGlobalClick(ev) {
        if (ev.target.closest('.dropdown, .o_dropdown_kanban')) {
            return;
        }

        // Add smooth animation
        const card = ev.currentTarget;
        card.style.transform = 'scale(0.98)';
        card.style.transition = 'transform 0.1s ease-in-out';

        setTimeout(() => {
            card.style.transform = '';
        }, 100);

        await super.onGlobalClick(ev);
    }

    // Add hover effects
    onMouseEnter(ev) {
        const card = ev.currentTarget;
        card.classList.add('hovered');
    }

    onMouseLeave(ev) {
        const card = ev.currentTarget;
        card.classList.remove('hovered');
    }
}

class PatientFileEnhancedRenderer extends KanbanRenderer {
    static components = {
        ...KanbanRenderer.components,
        KanbanRecord: PatientFileEnhancedRecord,
    };

    setup() {
        super.setup();
        this.state = useState({
            viewMode: 'comfortable', // comfortable, compact, detailed
            sortBy: 'date_in',
            filterBy: 'all'
        });
    }

    onMounted() {
        super.onMounted();
        this.initializeAnimations();
    }

    initializeAnimations() {
        // Add stagger animation to cards
        const cards = this.el.querySelectorAll('.o_patient_enhanced_card');
        cards.forEach((card, index) => {
            card.style.animationDelay = `${index * 0.05}s`;
            card.classList.add('fade-in-up');
        });
    }

    async onWillUpdateProps(nextProps) {
        await super.onWillUpdateProps(nextProps);
        // Re-initialize animations on data update
        setTimeout(() => this.initializeAnimations(), 100);
    }
}

class PatientFileEnhancedController extends KanbanController {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.notification = useService("notification");

        this.state = useState({
            isLoading: false,
            stats: {
                total: 0,
                open: 0,
                closed: 0,
                inpatient: 0,
                icu: 0
            }
        });

        onWillStart(this.onWillStart);
    }

    async onWillStart() {
        await this.loadStats();
    }

    async loadStats() {
        try {
            this.state.isLoading = true;
            const stats = await this.orm.call(
                "patient.file",
                "get_kanban_stats",
                [],
                {}
            );
            this.state.stats = { ...this.state.stats, ...stats };
        } catch (error) {
            console.error("Error loading stats:", error);
            this.notification.add("Error loading statistics", { type: "danger" });
        } finally {
            this.state.isLoading = false;
        }
    }

    async reload(params = {}) {
        const result = await super.reload(params);
        await this.loadStats();
        return result;
    }
}

export const PatientFileEnhancedKanbanView = {
    ...kanbanView,
    Controller: PatientFileEnhancedController,
    Renderer: PatientFileEnhancedRenderer,
};

registry.category("views").add("patient_file_kanban_view", PatientFileEnhancedKanbanView);