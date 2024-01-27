class State {
    constructor(name, {enter, exit, submit}) {
        this.name = name;
        this.enter = enter;
        this.exit = exit;
        this.submit = submit;
    }
}

class StateMachine {
    constructor() {
        this.states = {};
        this.current_state = null;
    }

    add_states(state_list) {
        state_list.forEach(element => {
            this.states[element.name] = element;
        });
        console.log(this.states);
    }

    transition(statename) {
        if (this.current_state != null) {
            console.log(`${this.current_state.name}.exit()`);
            this.current_state.exit?.();
        }
        this.current_state = this.states[statename];
        console.log(`${this.current_state.name}.enter()`);
        this.current_state.enter?.();
    }

    submit() {
        this.current_state?.submit?.();
    }
}