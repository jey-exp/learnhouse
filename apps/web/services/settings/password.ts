import { getAPIUrl } from '@services/config/config'
import {
  RequestBodyWithAuthHeader,
  errorHandling,
} from '@services/utils/ts/requests'
import toast from 'react-hot-toast'

/*
 This file includes only POST, PUT, DELETE requests
 GET requests are called from the frontend using SWR (https://swr.vercel.app/)
*/

export async function updatePassword(
  user_id: string,
  data: any,
  access_token: any
) {
  const toastId = toast.loading("Changing...")
  try {
    const result: any = await fetch(
      `${getAPIUrl()}users/change_password/` + user_id,
      RequestBodyWithAuthHeader('PUT', data, null, access_token)
    )
    toast.success("Password changed", {id:toastId})
    const res = await errorHandling(result)
    return res
  } catch (error) {
    toast.error("Couldn't change password", {id:toastId})
  }
}
