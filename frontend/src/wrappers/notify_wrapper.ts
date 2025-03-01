import { notify as notiwind_notify } from "notiwind";
import NotificationsTypes from '@/types/Notifications.interface';



export function notify(notify_args:NotificationsTypes, duration_ms:number) : ()=>void {

    //FYI, notify() returns a callback, that when called, closes the notification
    return notiwind_notify(notify_args as any, duration_ms);
}