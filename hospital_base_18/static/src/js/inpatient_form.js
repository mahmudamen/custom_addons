/** @odoo-module **/

import { Component, useState, onMounted } from "@odoo/owl";

export class SimplePatientCarousel extends Component {
    static template = "hospital_base.SimpleCarousel";

    setup() {
        this.state = useState({
            currentIndex: 0
        });

        onMounted(() => {
            this.startAutoplay();
        });
    }

    startAutoplay() {
        setInterval(() => {
            this.next();
        }, 5000);
    }

    next() {
        const itemCount = 4; // Number of carousel items
        this.state.currentIndex = (this.state.currentIndex + 1) % itemCount;
    }
}