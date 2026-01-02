package com.agent.misevolution.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 统一响应结果
 *
 * @author Maruiful
 * @version 1.0.0
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Result<T> {

    /**
     * 响应码
     */
    private Integer code;

    /**
     * 响应消息
     */
    private String message;

    /**
     * 响应数据
     */
    private T data;

    /**
     * 时间戳
     */
    private Long timestamp;

    /**
     * 成功响应
     *
     * @param message 消息
     * @param data    数据
     * @return 响应结果
     */
    public static <T> Result<T> success(String message, T data) {
        return Result.<T>builder()
                .code(200)
                .message(message)
                .data(data)
                .timestamp(System.currentTimeMillis())
                .build();
    }

    /**
     * 成功响应（无消息）
     *
     * @param data 数据
     * @return 响应结果
     */
    public static <T> Result<T> success(T data) {
        return success("success", data);
    }

    /**
     * 成功响应（无数据）
     *
     * @param message 消息
     * @return 响应结果
     */
    public static <T> Result<T> success(String message) {
        return success(message, null);
    }

    /**
     * 错误响应
     *
     * @param message 错误消息
     * @return 响应结果
     */
    public static <T> Result<T> error(String message) {
        return Result.<T>builder()
                .code(500)
                .message(message)
                .data(null)
                .timestamp(System.currentTimeMillis())
                .build();
    }

    /**
     * 错误响应（带错误码）
     *
     * @param code    错误码
     * @param message 错误消息
     * @return 响应结果
     */
    public static <T> Result<T> error(Integer code, String message) {
        return Result.<T>builder()
                .code(code)
                .message(message)
                .data(null)
                .timestamp(System.currentTimeMillis())
                .build();
    }

    /**
     * 判断是否成功
     *
     * @return 是否成功
     */
    public boolean isSuccess() {
        return code != null && code == 200;
    }
}
