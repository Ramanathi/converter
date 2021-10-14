function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

const convert = document.getElementById("convert")
const progress = document.getElementById("progress")
convert.addEventListener("click",async function(){
    await sleep(2000); // this is used to ensure if link is pasted, if not page refreshes before showing the progress
    progress.style.display="block";
});