const { promisify } = require('util');

module.exports.sendTwilioSms = async function sendTwilioSms(messageBody) {
    const sid = process.env.TWILIO_SID;
    const token = process.env.TWILIO_TOKEN;
    const from = process.env.TWILIO_FROM;
    const to = process.env.TWILIO_TO;

    if (!sid || !token || !from || !to) {
        console.log('[twilio_util] TWILIO not configured:\n', messageBody);
        return null
    }

    const client = require('twilio')(sid, token);
    const msg = await client.messages.create({body: messageBody, from, to});
    console.log('[twilio_util] Sent SMS, sid:', msg.sid);
    return msg.sid;
};
