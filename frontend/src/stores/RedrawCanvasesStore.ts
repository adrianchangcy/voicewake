import { defineStore } from 'pinia';

type RedrawCanvasesTypes = {
    [index:number]: ()=>any
}



//we group all canvas-related callbacks into this store
//then we can just use one single event listener or mutationObserver at BaseApp and run all of them
//when we add new canvas to this store, return index so the component can delete on beforeUnmount()



export const useRedrawCanvasesStore = defineStore('redraw_canvases_store', {
    state: ()=>({
        audio_volume_peak_canvases: {} as RedrawCanvasesTypes,
    }),
    getters: {
        getAudioVolumePeakCanvases: (state) => {
            return state.audio_volume_peak_canvases;
        },
    },
    actions: {
        redrawAllAudioVolumePeakCanvases() : void {

            const indexes = Object.keys(this.audio_volume_peak_canvases);

            if(indexes.length === 0){

                return;
            }

            for(let x=0; x < indexes.length; x++){

                this.audio_volume_peak_canvases[Number(indexes[x])]();
            }
        },
        addAudioVolumePeakCanvas(passed_callback:()=>any) : number {

            const latest_index = Object.keys(this.audio_volume_peak_canvases).length;

            this.audio_volume_peak_canvases[latest_index] = passed_callback;

            //save this at component-level to delete on beforeUnmount()
            return latest_index;
        },
        deleteAudioVolumePeakCanvas(index:number) : void {

            delete this.audio_volume_peak_canvases[index];
        },
    },
    persist: false,
});