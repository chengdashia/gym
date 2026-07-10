import { uploadFile } from '@/utils/request';

export const uploadApi = {
  image(filePath: string, usage: 'food_recognition' | 'diet_record' | 'avatar', temporary = true) {
    return uploadFile(filePath, { usage_type: usage, temporary });
  },
  avatar(filePath: string) {
    return uploadFile(filePath, {
      usage_type: 'avatar',
      temporary: false,
    });
  },
};
