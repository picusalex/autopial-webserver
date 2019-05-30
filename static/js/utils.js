

function pretty_millisecondsDisplay(nDiff) {
  var oResult = {};

  // Get diff in days
  oResult.days = Math.floor(nDiff / 1000 / 60 / 60 / 24);
  nDiff -= oResult.days * 1000 * 60 * 60 * 24;

  // Get diff in hours
  oResult.hours = Math.floor(nDiff / 1000 / 60 / 60);
  nDiff -= oResult.hours * 1000 * 60 * 60;

  // Get diff in minutes
  oResult.minutes = Math.floor(nDiff / 1000 / 60);
  nDiff -= oResult.minutes * 1000 * 60;

  // Get diff in seconds
  oResult.seconds = Math.floor(nDiff / 1000);

  // Render the diffs into friendly duration string

  // Days
  var sDays = '00';
  if (oResult.days > 0) {
      sDays = String(oResult.days);
  }
  if (sDays.length === 1) {
      sDays = '0' + sDays;
  }

  // Format Hours
  var sHour = '00';
  if (oResult.hours > 0) {
      sHour = String(oResult.hours);
  }
  if (sHour.length === 1) {
      sHour = '0' + sHour;
  }

  //  Format Minutes
  var sMins = '00';
  if (oResult.minutes > 0) {
      sMins = String(oResult.minutes);
  }
  if (sMins.length === 1) {
      sMins = '0' + sMins;
  }

  //  Format Seconds
  var sSecs = '00';
  if (oResult.seconds > 0) {
      sSecs = String(oResult.seconds);
  }
  if (sSecs.length === 1) {
      sSecs = '0' + sSecs;
  }

  //  Set Duration
  var sDuration = sDays + ':' + sHour + ':' + sMins + ':' + sSecs;
  oResult.duration = sDuration;

  var sHumanDuration = sDays + 'd ' + sHour + 'h ' + sMins + 'm ' + sSecs;
  oResult.human_duration = sHumanDuration;

  var sSimpleDuration = "";
  var fullHours = oResult.days * 24 + oResult.hours;
  if (fullHours != 0) {
    sSimpleDuration = sSimpleDuration + fullHours + "h "
  }
  if (oResult.minutes != 0) {
    sSimpleDuration = sSimpleDuration + oResult.minutes + "m "
  }
  sSimpleDuration = sSimpleDuration + sSecs + "s"
  oResult.simple_duration = sSimpleDuration;

  // Set friendly text for printing
  if(oResult.days === 0) {

      if(oResult.hours === 0) {

          if(oResult.minutes === 0) {
              var sSecHolder = oResult.seconds > 1 ? 'Seconds' : 'Second';
              oResult.friendlyNiceText = oResult.seconds + ' ' + sSecHolder;
          } else {
              var sMinutesHolder = oResult.minutes > 1 ? 'Minutes' : 'Minute';
              oResult.friendlyNiceText = oResult.minutes + ' ' + sMinutesHolder;
          }

      } else {
          var sHourHolder = oResult.hours > 1 ? 'Hours' : 'Hour';
          var sMinutesHolder = oResult.minutes > 1 ? 'Minutes' : 'Minute';
          oResult.friendlyNiceText = oResult.hours + ' ' + sHourHolder + ' ' + oResult.minutes + ' ' + sMinutesHolder;
      }
  } else {
      var sDayHolder = oResult.days > 1 ? 'Days' : 'Day';
      var sHourHolder = oResult.hours > 1 ? 'Hours' : 'Hour';
      var sMinutesHolder = oResult.minutes > 1 ? 'Minutes' : 'Minute';
      oResult.friendlyNiceText = oResult.days + ' ' + sDayHolder + ' ' +oResult.hours + ' ' + sHourHolder + ' ' + oResult.minutes + ' ' + sMinutesHolder;
  }

  return oResult;
}

function pretty_timeDifference(strtdatetime) {
  var datetime = new Date(strtdatetime);
  var oResult = {};

  var oToday = new Date();

  var nDiff = oToday.getTime() - datetime.getTime();

  return pretty_millisecondsDisplay(nDiff);
}


function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];

    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function formatBps(bps, decimals = 2) {
    if (bps === 0) return '0 kbps';

    bps = bps / 1024.0

    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['kbps', 'Mbps', 'Gbps'];

    const i = Math.floor(Math.log(bps) / Math.log(k));

    if (bps < 1) return bps.toFixed(dm)+' kbps'
    return parseFloat((bps / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function pretty_dateDisplay(strtdatetime) {
    var dt = new Date(strtdatetime);
    var months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    var days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    return days[dt.getDay()] + " " + dt.getDate() + " " + months[dt.getMonth()] + " " + dt.getFullYear() + " at " + dt.getHours() + ":" + dt.getMinutes();

}