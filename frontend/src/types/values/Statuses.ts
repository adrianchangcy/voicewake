//best way to use this is to store the values you need in component
//then, with an arg with the same type as this, check via "" in this.statuses
type Statuses = "" | "no_event_rooms" | "replying" | "replying_successful" | "expired" | "deleted";

export default Statuses;